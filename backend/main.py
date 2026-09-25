from pathlib import Path
"""H1-AI — Main FastAPI App (hardened).

Fixes:
- register endpoint uses DB (was broken with _UsersDBProxy)
- CORS validation in production
- docs disabled in production
"""
from contextlib import asynccontextmanager
from pathlib import Path as _Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
import structlog

from config import settings
from config_loader import prod_config
from auth.dependencies import (
    seed_users,
)
from knowledge.engine import advisory_engine
from middleware.rate_limit import limiter
from middleware.auth_context import AuthContextMiddleware
from middleware.timing import TimingMiddleware
from middleware.request_id import RequestContextMiddleware
from middleware.rate_limit_headers import RateLimitHeadersMiddleware
from api.health_routes import router as health_router
from config_validator import validate_and_report
from session.session_store import session_store
from services.logging_service import setup_logging

from api.whatsapp_routes import router as whatsapp_router
from api.whatsapp_webhook import router as whatsapp_webhook_router
from api.whatsapp_webhook_v2 import router as whatsapp_webhook_v2_router
from api.user_routes import router as user_router
from api.audit_routes import router as audit_router
from api.chat_routes import router as chat_router
from api.voice_routes import router as voice_router
from api.tunnel_routes import router as tunnel_router
from api.analytics_routes import router as analytics_router
from api.tenant_middleware import TenantMiddleware
from api.chat_stream import router as chat_stream_router
from api.whatsapp_chatbot import router as whatsapp_chatbot_router
from admin.api.products_routes import router as admin_products_router
from admin.api.drugs_routes import router as admin_drugs_router
from admin.api.interactions_routes import router as admin_interactions_router
from admin.api.conditions_routes import router as admin_conditions_router
from admin.api.synonyms_routes import router as admin_synonyms_router
from admin.api.audit_routes import router as admin_audit_router
from admin.api.export_routes import router as admin_export_router
from admin.api.import_routes import router as admin_import_router

# DB imports for register endpoint
from routers.auth import router as auth_router
from routers.chat import router as chat_router_v2
from routers.knowledge import router as knowledge_router
from routers.cache import router as cache_router
from routers.system import router as system_router
from routers.admin.settings import router as admin_settings_router
from routers.admin.api_keys import router as admin_api_keys_router
from routers.admin.subscriptions import router as admin_subscriptions_router
from routers.admin.alerts import router as admin_alerts_router
from routers.admin.pharmacies import router as admin_pharmacies_router
from routers.admin.whatsapp_numbers import router as admin_wa_numbers_router
from routers.admin.whatsapp_service import router as admin_wa_service_router
from routers.admin.live_feed import router as admin_live_feed_router
from routers.whatsapp_public import router as whatsapp_public_router
from routers.admin.feature_flags import router as admin_feature_flags_router
from routers.admin.notifications import router as admin_notifications_router
from routers.admin.inbox import router as admin_inbox_router
from routers.super_admin import router as super_admin_router
from routers.pharmacy_admin import router as pharmacy_admin_router

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

app.add_middleware(TenantMiddleware)


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
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(tunnel_router)
app.include_router(analytics_router)
app.include_router(chat_stream_router)
app.include_router(whatsapp_chatbot_router)
app.include_router(auth_router)
app.include_router(chat_router_v2)
app.include_router(knowledge_router)
app.include_router(cache_router)
app.include_router(system_router)
app.include_router(admin_settings_router)
app.include_router(admin_api_keys_router)
app.include_router(admin_subscriptions_router)
app.include_router(admin_alerts_router)
app.include_router(admin_pharmacies_router)
app.include_router(admin_wa_numbers_router)
app.include_router(admin_wa_service_router)
app.include_router(admin_live_feed_router)
app.include_router(whatsapp_public_router)
app.include_router(admin_wa_numbers_router)
app.include_router(admin_feature_flags_router)
app.include_router(admin_notifications_router)
app.include_router(admin_inbox_router)
app.include_router(super_admin_router)
app.include_router(pharmacy_admin_router)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "طلبات كثيرة جدًا. حاول بعد دقيقة."},
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

    @app.get("/pharmacy")
    @app.get("/pharmacy/")
    async def _pharmacy_admin_index():
        """Pharmacy Admin panel — per-tenant management."""
        return FileResponse(str(_admin_static / "pharmacy.html"))

    ALLOWED_SUPER_IPS = {
        "127.0.0.1", "::1",
        "192.168.1.17", "192.168.1.24",
        "100.94.32.49",
    }

    @app.get("/super")
    @app.get("/super/")
    async def _super_admin_index(request: Request):
        """Super Admin panel — restricted by IP."""
        client_ip = request.client.host if request.client else None
        if client_ip not in ALLOWED_SUPER_IPS:
            logger.warning("super.access_denied", ip=client_ip)
            raise HTTPException(404, "Not Found")
        return FileResponse(str(_admin_static / "super.html"))

    @app.get("/api/super/config")
    async def _super_config(request: Request):
        """Super Admin config — restricted by IP."""
        client_ip = request.client.host if request.client else None
        if client_ip not in ALLOWED_SUPER_IPS:
            raise HTTPException(404, "Not Found")

        # بيانات ثابتة للدخول التلقائي
        return {
            "auto_login": True,
            "username": "abdelhameidmaher",
        }




# ═══════════════════════════════════════════════════════════
# SETTINGS MANAGEMENT
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# CUSTOMER INTERFACE (Public)
# ═══════════════════════════════════════════════════════════
_customer_static = _Path(__file__).parent / "customer" / "static"
if _customer_static.exists():
    app.mount("/customer/static", StaticFiles(directory=str(_customer_static)), name="customer_static")

    @app.get("/")
    async def _customer_landing():
        """Landing page for customers."""
        return FileResponse(str(_customer_static / "index.html"))

    @app.get("/chat")
    async def _customer_chat():
        """Customer chat interface."""
        return FileResponse(str(_customer_static / "chat.html"))

    @app.get("/login")
    async def _customer_login():
        """Login page — redirect to admin login for now."""
        return FileResponse(str(_customer_static / "login.html"))

# ═══════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# CHAT & KNOWLEDGE
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# MULTI-PHARMACY MANAGEMENT
# ═══════════════════════════════════════════════════════════
# (moved to routers/admin/pharmacies.py)


# ═══════════════════════════════════════════════════════════
# PUBLIC SELF-SERVICE ONBOARDING
# ═══════════════════════════════════════════════════════════

# /public/static mount moved to keep for backward compatibility
_public_static = _Path(__file__).parent / "public" / "static"
if _public_static.exists():
    app.mount("/public/static", StaticFiles(directory=str(_public_static)), name="public_static")


# ═══════════════════════════════════════════════════════════
# WHATSAPP SESSION LIFECYCLE
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# PRIVACY POLICY + TERMS
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# DATABASE EXPANSION ENDPOINTS
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# API KEYS CRUD
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# CACHE MANAGEMENT
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
#  Static files for chat UI
# ═══════════════════════════════════════════════════════════
_chat_static_dir = Path(__file__).parent / "static" / "chat"
if _chat_static_dir.exists():
    app.mount(
        "/static/chat",
        StaticFiles(directory=str(_chat_static_dir)),
        name="chat-static",
    )
