"""Auth routes — login, register, refresh, me."""
from fastapi import APIRouter, Depends, HTTPException, Request

from config import settings
from models.schemas import (
    LoginRequest, RegisterRequest, RefreshRequest, Token, User,
)
from auth.models import UserInDB
from auth.jwt_handler import (
    verify_password, hash_password,
    create_access_token, create_refresh_token, decode_token,
)
from auth.dependencies import (
    get_current_user, get_user_by_username, get_user_by_id,
)
from middleware.rate_limit import limiter
from services.metrics import metrics
from db import SessionLocal
from db.repositories import UserRepository

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _make_token_response(user_db: UserInDB) -> Token:
    return Token(
        access_token=create_access_token(
            user_db.id, user_db.username, user_db.role,
            pharmacy_id=user_db.pharmacy_id,
        ),
        refresh_token=create_refresh_token(
            user_db.id, user_db.username, user_db.role,
            pharmacy_id=user_db.pharmacy_id,
        ),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=User(**user_db.model_dump(exclude={"hashed_password"})),
    )


@router.post("/login", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
async def login(request: Request, req: LoginRequest):
    user_db = get_user_by_username(req.username)
    if not user_db or not verify_password(req.password, user_db.hashed_password):
        metrics.record_login(success=False)
        try:
            from api.chat_routes import log_audit
            await log_audit(
                user_id="00000000-0000-0000-0000-000000000000",
                username=req.username[:50],
                action="login_failed",
                entity="user",
                entity_id=req.username[:50],
                details="Invalid credentials",
            )
        except Exception as _e:
            import structlog
            structlog.get_logger().warning("login_audit_failed", error=str(_e)[:150])
        
        raise HTTPException(status_code=401, detail="بيانات دخول غلط")
    if not user_db.is_active:
        raise HTTPException(status_code=403, detail="الحساب معطّل")
    metrics.record_login(success=True)
    return _make_token_response(user_db)


@router.post("/register", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
async def register(request: Request, req: RegisterRequest):
    """Register new user — uses DB."""
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if repo.get_by_username(req.username):
            raise HTTPException(status_code=400, detail="اسم المستخدم موجود")

        new_user = repo.create(
            username=req.username,
            hashed_password=hash_password(req.password),
            role="customer",
            full_name=req.full_name or "",
        )

        user_db = UserInDB(
            id=new_user.id,
            username=new_user.username,
            role=new_user.role,
            full_name=new_user.full_name or "",
            is_active=new_user.is_active,
            hashed_password=new_user.hashed_password,
        )
        return _make_token_response(user_db)
    finally:
        db.close()


@router.post("/refresh", response_model=Token)
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_db = get_user_by_id(payload.sub)
    if not user_db or not user_db.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return _make_token_response(user_db)


@router.get("/me", response_model=User)
async def me(user: User = Depends(get_current_user)):
    return user
