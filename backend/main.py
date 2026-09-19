"""H1-AI — Main FastAPI App (hardened).

Fixes:
- register endpoint uses DB (was broken with _UsersDBProxy)
- CORS validation in production
- docs disabled in production
"""
from contextlib import asynccontextmanager
from uuid import uuid4
from pathlib import Path as _Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
    require_admin,
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
from services.chat_cache import chat_cache
from services.settings_service import settings_service

from api.whatsapp_routes import router as whatsapp_router
from api.whatsapp_webhook import router as whatsapp_webhook_router
from api.whatsapp_webhook_v2 import router as whatsapp_webhook_v2_router
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

# DB imports for register endpoint
from db import SessionLocal
from db.repositories import UserRepository

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not validate_and_report():
        raise RuntimeError("Invalid configuration")

    logger.info(
        "app.startup",
        app_name=prod_config.app_name,
        environment=settings.environment,
    )

    # Validate CORS in production
    if settings.is_production and "*" in settings.cors_origins:
        raise RuntimeError("CORS wildcard '*' not allowed in production!")

    advisory_engine.initialize()
    seed_users()
    logger.info("app.ready")
    yield
    session_store.cleanup_expired()
    logger.info("app.shutdown")


app = FastAPI(
    title=prod_config.app_name,
    version="5.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# ─── Middleware (order matters: last added = first executed) ───
app.add_middleware(RateLimitHeadersMiddleware)
app.add_middleware(AuthContextMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600,
)

app.state.limiter = limiter

# ─── Routers ───
app.include_router(whatsapp_router)
app.include_router(whatsapp_webhook_router)
app.include_router(whatsapp_webhook_v2_router)
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
_admin_static = _Path(__file__).parent / "admin" / "static"
if _admin_static.exists():
    app.mount("/admin/static", StaticFiles(directory=str(_admin_static)), name="admin_static")

    @app.get("/admin")
    @app.get("/admin/")
    async def _admin_index():
        return FileResponse(str(_admin_static / "index.html"))
    
    @app.get("/admin/dashboard")
    async def _admin_dashboard():
        return FileResponse(str(_admin_static / "index.html"))




# ═══════════════════════════════════════════════════════════
# SETTINGS MANAGEMENT
# ═══════════════════════════════════════════════════════════
@app.get("/v1/admin/settings")
async def get_settings(user: User = Depends(require_admin)):
    """Get all settings."""
    return {
        "whatsapp": settings_service.get_whatsapp(),
        "app": settings_service.load().get("app", {}),
        "features": settings_service.load().get("features", {}),
    }


@app.get("/v1/admin/settings/whatsapp")
async def get_whatsapp_settings(user: User = Depends(require_admin)):
    """Get WhatsApp settings."""
    return settings_service.get_whatsapp()


@app.put("/v1/admin/settings/whatsapp")
async def update_whatsapp_settings(
    request: Request,
    user: User = Depends(require_admin),
):
    """Update WhatsApp settings."""
    try:
        updates = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Validate
    if "phone" in updates:
        phone = str(updates["phone"]).strip()
        if phone and not (phone.startswith("+") or phone.isdigit()):
            raise HTTPException(
                status_code=400,
                detail="Phone must start with + or be digits",
            )
        updates["phone"] = phone

    if "mode" in updates:
        if updates["mode"] not in ("link", "qr", "api"):
            raise HTTPException(
                status_code=400,
                detail="Mode must be link, qr, or api",
            )

    if "enabled" in updates:
        updates["enabled"] = bool(updates["enabled"])

    result = settings_service.update_whatsapp(updates)
    return {"success": True, "whatsapp": result}

# ═══════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.post("/v1/auth/login", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
async def login(request: Request, req: LoginRequest):
    user_db = get_user_by_username(req.username)
    if not user_db or not verify_password(req.password, user_db.hashed_password):
        metrics.record_login(success=False)
        raise HTTPException(status_code=401, detail="بيانات دخول غلط")
    if not user_db.is_active:
        raise HTTPException(status_code=403, detail="الحساب معطّل")
    metrics.record_login(success=True)
    return _make_token_response(user_db)


@app.post("/v1/auth/register", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
async def register(request: Request, req: RegisterRequest):
    """Register new user — FIXED: uses DB instead of broken proxy."""
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


@app.post("/v1/auth/refresh", response_model=Token)
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_db = get_user_by_id(payload.sub)
    if not user_db or not user_db.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return _make_token_response(user_db)


@app.get("/v1/auth/me", response_model=User)
async def me(user: User = Depends(get_current_user)):
    return user


# ═══════════════════════════════════════════════════════════
# CHAT & KNOWLEDGE
# ═══════════════════════════════════════════════════════════
@app.post("/v1/chat", response_model=ChatResponse)
@limiter.limit(settings.rate_limit_chat)
async def chat(
    request: Request,
    req: ChatRequest,
    user: User = Depends(get_current_user),
):
    session_id = req.session_id or str(uuid4())
    
    # ═══ Check cache first ═══
    cached = chat_cache.get(req.message, user.role)
    if cached:
        session = session_store.get(session_id) or {"user_id": user.id, "messages": []}
        session["messages"].append({"role": "user", "content": req.message})
        session["messages"].append({"role": "agent", "content": cached["data"]["text"]})
        session_store.set(session_id, session)
        return ChatResponse(
            data=cached["data"],
            user_type=cached["user_type"],
            session_id=session_id,
            route_method="cache",
            handler=cached["handler"],
        )
    
    try:
        # Run orchestrator in thread pool to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: orchestrator.handle(req.message, user_role=user.role),
        )
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

@app.post("/v1/chat/stream")
@limiter.limit(settings.rate_limit_chat)
async def chat_stream(
    request: Request,
    req: ChatRequest,
    user: User = Depends(get_current_user),
):
    """Streaming chat endpoint using Server-Sent Events (SSE)."""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    async def event_generator():
        session_id = req.session_id or str(uuid4())
        
        # 1. Start event
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        
        try:
            # 2. Process (in thread pool)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: orchestrator.handle(req.message, user_role=user.role),
            )
            
            text = result.response.text or ""
            
            # 3. Stream chunks (2-3 chars at a time for smooth feel)
            chunk_size = 2
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.015)
            
            # 4. Save session
            session = session_store.get(session_id) or {"user_id": user.id, "messages": []}
            session["messages"].append({"role": "user", "content": req.message})
            session["messages"].append({"role": "agent", "content": text})
            session_store.set(session_id, session)
            
            # 5. Done event with metadata
            done_data = {
                'type': 'done',
                'session_id': session_id,
                'handler': result.handler,
                'confidence': result.response.confidence,
                'needs_human': result.response.needs_human,
                'action': result.response.action,
                'products_referenced': result.response.products_referenced or [],
            }
            yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error("chat_stream.error", error=str(e), user=user.id)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



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


# ═══════════════════════════════════════════════════════════
# CACHE MANAGEMENT
# ═══════════════════════════════════════════════════════════
@app.get("/v1/cache/stats")
async def cache_stats(user: User = Depends(require_admin)):
    """Get chat cache statistics."""
    return chat_cache.stats()


@app.post("/v1/cache/clear")
async def cache_clear(user: User = Depends(require_admin)):
    """Clear chat cache."""
    chat_cache.clear()
    return {"success": True, "message": "Cache cleared"}


@app.post("/v1/cache/save")
async def cache_save(user: User = Depends(require_admin)):
    """Save cache to disk."""
    chat_cache.save_to_disk()
    return {"success": True}

