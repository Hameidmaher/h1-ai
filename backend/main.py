"""H1-AI — Main FastAPI App."""
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi.errors import RateLimitExceeded
import structlog

from config import settings
from config_loader import prod_config
from models.schemas import (
    ChatRequest, ChatResponse, LoginRequest, RegisterRequest,
    RefreshRequest, Token, User, KnowledgeSearchRequest,
    KnowledgeAdviseRequest,
)
from auth.models import UserInDB
from auth.jwt_handler import (
    verify_password, hash_password, create_access_token,
    create_refresh_token, decode_token,
)
from auth.dependencies import (
    get_current_user, get_user_by_username, get_user_by_id,
    _users_db, seed_users,
)
from knowledge.engine import advisory_engine
from core.orchestrator import orchestrator
from middleware.rate_limit import limiter
from middleware.auth_context import AuthContextMiddleware
from middleware.timing import TimingMiddleware
from middleware.request_id import RequestContextMiddleware
from middleware.rate_limit_headers import RateLimitHeadersMiddleware
from api.health_routes import router as health_router
from config_validator import validate_and_report
from session.session_store import session_store
from services.logging_service import setup_logging
from services.metrics import metrics
from api.whatsapp_routes import router as whatsapp_router
from api.whatsapp_webhook import router as whatsapp_webhook_router
from api.user_routes import router as user_router
from api.audit_routes import router as audit_router
from admin.api.products_routes import router as admin_products_router
from admin.api.drugs_routes import router as admin_drugs_router
from admin.api.interactions_routes import router as admin_interactions_router
from admin.api.conditions_routes import router as admin_conditions_router
from admin.api.synonyms_routes import router as admin_synonyms_router
from admin.api.audit_routes import router as admin_audit_router
from admin.api.export_routes import router as admin_export_router
from admin.api.import_routes import router as admin_import_router

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not validate_and_report():
        raise RuntimeError("Invalid configuration")
    logger.info("app.startup", app_name=prod_config.app_name)
    advisory_engine.initialize()
    seed_users()
    logger.info("app.ready")
    yield
    session_store.cleanup_expired()
    logger.info("app.shutdown")


app = FastAPI(
    title=prod_config.app_name,
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not prod_config.is_production else None,
)

app.add_middleware(TimingMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(AuthContextMiddleware)
app.add_middleware(RateLimitHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.include_router(whatsapp_router)
app.include_router(health_router)
app.include_router(admin_products_router)
app.include_router(admin_drugs_router)
app.include_router(admin_interactions_router)
app.include_router(admin_conditions_router)
app.include_router(admin_synonyms_router)
app.include_router(admin_audit_router)
app.include_router(admin_export_router)
app.include_router(admin_import_router)
app.include_router(user_router)
app.include_router(audit_router)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "طلبات كثيرة جدًا. حاول بعد دقيقة."},
    )





def _make_token_response(user_db: UserInDB) -> Token:
    return Token(
        access_token=create_access_token(user_db.id, user_db.username, user_db.role),
        refresh_token=create_refresh_token(user_db.id, user_db.username, user_db.role),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=User(**user_db.model_dump(exclude={"hashed_password"})),
    )




# ═══════════════════════════════════════════════════════════
# ADMIN UI (Static Files)
# ═══════════════════════════════════════════════════════════
from pathlib import Path as _Path

_admin_static = _Path(__file__).parent / "admin" / "static"
if _admin_static.exists():
    app.mount("/admin/static", StaticFiles(directory=str(_admin_static)), name="admin_static")

    @app.get("/admin")
    @app.get("/admin/")
    async def _admin_index():
        return FileResponse(str(_admin_static / "index.html"))

@app.post("/v1/auth/login", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
async def login(request: Request, req: LoginRequest):
    user_db = get_user_by_username(req.username)
    if not user_db or not verify_password(req.password, user_db.hashed_password):
        metrics.record_login(success=False)
        raise HTTPException(status_code=401, detail="بيانات دخول غلط")
    metrics.record_login(success=True)
    return _make_token_response(user_db)


@app.post("/v1/auth/register", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
async def register(request: Request, req: RegisterRequest):
    if get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود")
    user_id = str(uuid4())
    user_db = UserInDB(
        id=user_id, username=req.username, role="customer",
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
    )
    _users_db[user_id] = user_db
    return _make_token_response(user_db)


@app.post("/v1/auth/refresh", response_model=Token)
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_db = get_user_by_id(payload.sub)
    if not user_db or not user_db.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return _make_token_response(user_db)


@app.get("/v1/auth/me", response_model=User)
async def me(user: User = Depends(get_current_user)):
    return user


@app.post("/v1/chat", response_model=ChatResponse)
@limiter.limit(settings.rate_limit_chat)
async def chat(
    request: Request,
    req: ChatRequest,
    user: User = Depends(get_current_user),
):
    session_id = req.session_id or str(uuid4())
    try:
        result = orchestrator.handle(req.message, user_role=user.role)
        session = session_store.get(session_id) or {
            "user_id": user.id, "messages": []
        }
        session["messages"].append({"role": "user", "content": req.message})
        session["messages"].append({"role": "agent", "content": result.response.text})
        session_store.set(session_id, session)
        return ChatResponse(
            data=result.response,
            user_type=result.user_type,
            session_id=session_id,
            route_method=result.route_method,
            handler=result.handler,
        )
    except Exception as e:
        logger.error("chat.error", error=str(e), user=user.id)
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")


@app.post("/v1/knowledge/search")
async def knowledge_search(
    req: KnowledgeSearchRequest,
    user: User = Depends(get_current_user),
):
    results = advisory_engine.search(req.query, top_k=req.top_k)
    return {"query": req.query, "count": len(results), "results": results}


@app.post("/v1/knowledge/advise")
async def knowledge_advise(
    req: KnowledgeAdviseRequest,
    user: User = Depends(get_current_user),
):
    result = advisory_engine.analyze(req.query)
    return result.to_dict()
