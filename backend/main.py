"""H1-AI — Main FastAPI App (hardened).

Fixes:
- register endpoint uses DB (was broken with _UsersDBProxy)
- CORS validation in production
- docs disabled in production
"""
from pathlib import Path
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
from api.monitoring_routes import router as monitoring_router
from api.monitoring_routes import record_request
from api.control_routes import router as control_router
from api.cc_data_routes import router as cc_data_router
from api.cc_users_routes import router as cc_users_router
from api.cc_settings_routes import router as cc_settings_router
from api.cc_search_routes import router as cc_search_router
from api.user_chat_routes import router as user_chat_router
from api.whatsapp_auth_routes import router as whatsapp_auth_router
from api.admin_chat_routes import router as admin_chat_router
from api.multi_role_chat_routes import router as multi_role_chat_router


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
app.include_router(admin_wa_service_router)
app.include_router(admin_live_feed_router)
app.include_router(whatsapp_public_router)
app.include_router(admin_wa_numbers_router)
app.include_router(admin_feature_flags_router)
app.include_router(admin_notifications_router)
app.include_router(admin_inbox_router)
app.include_router(super_admin_router)
app.include_router(pharmacy_admin_router)
app.include_router(monitoring_router)
app.include_router(control_router)
app.include_router(cc_data_router)
app.include_router(cc_users_router)
app.include_router(cc_settings_router)
app.include_router(cc_search_router)
app.include_router(user_chat_router)
app.include_router(whatsapp_auth_router)
app.include_router(admin_chat_router)
app.include_router(multi_role_chat_router)


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


# ═══════════════════════════════════════════════════════════════
# 📊 Middleware لتسجيل كل طلب في Monitoring
# ═══════════════════════════════════════════════════════════════
@app.middleware("http")
async def _monitoring_middleware(request: Request, call_next):
    """يسجّل كل طلب HTTP في الـ monitoring metrics."""
    import time
    start = time.time()
    try:
        response = await call_next(request)
        duration = (time.time() - start) * 1000  # ms
        # نتجاهل الـ monitoring نفسه (عشان مانعملش loop)
        if not request.url.path.startswith("/v1/monitoring"):
            record_request(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration,
            )
        return response
    except Exception as e:
        duration = (time.time() - start) * 1000
        record_request(
            method=request.method,
            path=request.url.path,
            status=500,
            duration_ms=duration,
        )
        raise

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

@app.get("/admin/monitor")
async def _admin_monitor():
    """Live monitoring dashboard."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    p = Path(__file__).parent / "admin" / "static" / "monitor.html"
    return FileResponse(str(p))

# ═══════════════════════════════════════════════════════════════
# 🎛️ Control Center Routes
# ═══════════════════════════════════════════════════════════════
from pathlib import Path as _Path

@app.get("/admin/control")
@app.get("/admin/control/")
async def _admin_control_center():
    """Control Center — Ultra Flexible Dashboard."""
    from fastapi.responses import FileResponse
    p = _Path(__file__).parent / "admin" / "static" / "control_center.html"
    return FileResponse(str(p))

# ═══════════════════════════════════════════════════════════════════
# 🏥 User Portal Routes (Login + Register + App)
# ═══════════════════════════════════════════════════════════════════
from pathlib import Path as _P2

_PORTAL = _P2(__file__).parent / "customer" / "portal"

@app.get("/login")
async def _portal_login():
    from fastapi.responses import FileResponse
    return FileResponse(str(_PORTAL / "login.html"))

@app.get("/register")
async def _portal_register():
    from fastapi.responses import FileResponse
    return FileResponse(str(_PORTAL / "register.html"))

@app.get("/app")
@app.get("/app/")
async def _portal_app():
    from fastapi.responses import FileResponse
    return FileResponse(str(_PORTAL / "app.html"))

@app.get("/")
async def _portal_root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")



# ═══════════════════════════════════════════════════════════════════
# 🎨 Design System — Static Files
# ═══════════════════════════════════════════════════════════════════
from pathlib import Path as _DS_Path
from fastapi.staticfiles import StaticFiles as _DS_Static

_DS_DIR = _DS_Path(__file__).parent / "static" / "design-system"
if _DS_DIR.exists():
    app.mount("/static/design-system", _DS_Static(directory=str(_DS_DIR)), name="design_system")
    print(f"✅ Design System mounted: {_DS_DIR}")
else:
    print(f"⚠️ Design System dir not found: {_DS_DIR}")

# ═══════════════════════════════════════════════════════════════════
# 📱 WhatsApp Proxy + Pharmacy Pages
# ═══════════════════════════════════════════════════════════════════
import httpx as _wa_httpx
from pathlib import Path as _WA_Path

_WA_URL = "http://localhost:3001"
_WA_PHARM = _WA_Path(__file__).parent / "customer" / "pharmacy"


@app.api_route("/api/whatsapp/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def _wa_proxy(path: str, request: Request):
    try:
        url = f"{_WA_URL}/{path}"
        async with _wa_httpx.AsyncClient(timeout=30) as client:
            body = None
            if request.method in ("POST", "PUT", "PATCH"):
                try:
                    body = await request.json()
                except Exception:
                    body = None
            r = await client.request(request.method, url, json=body)
            try:
                return JSONResponse(content=r.json(), status_code=r.status_code)
            except Exception:
                return JSONResponse(content={"raw": r.text}, status_code=r.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/pharmacy/whatsapp")
async def _pharm_whatsapp():
    from fastapi.responses import FileResponse
    p = _WA_PHARM / "whatsapp.html"
    if p.exists():
        return FileResponse(str(p))
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/pharmacy/dashboard")
async def _pharm_dashboard():
    from fastapi.responses import FileResponse
    p = _WA_PHARM / "dashboard.html"
    if p.exists():
        return FileResponse(str(p))
    return JSONResponse({"error": "coming soon", "redirect": "/pharmacy/whatsapp"}, status_code=404)

@app.get("/pharmacy/dashboard")
async def _pharmacy_dashboard():
    from fastapi.responses import FileResponse
    from pathlib import Path
    p = Path(__file__).parent / "customer" / "pharmacy" / "dashboard.html"
    if p.exists():
        return FileResponse(str(p))
    return JSONResponse({"error": "not found"}, status_code=404)

