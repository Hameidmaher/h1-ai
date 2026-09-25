from pathlib import Path
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
    seed_users,
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
from services.pharmacy_service import pharmacy_service
from services.whatsapp_bridge import whatsapp_bridge
from services.live_feed import live_feed

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
from db import SessionLocal
from db.repositories import UserRepository
from routers.auth import router as auth_router
from routers.chat import router as chat_router_v2
from routers.knowledge import router as knowledge_router
from routers.cache import router as cache_router
from routers.system import router as system_router
from routers.admin.settings import router as admin_settings_router
from routers.admin.api_keys import router as admin_api_keys_router
from routers.admin.subscriptions import router as admin_subscriptions_router
from routers.admin.alerts import router as admin_alerts_router
from routers.admin.feature_flags import router as admin_feature_flags_router
from routers.admin.notifications import router as admin_notifications_router
from routers.admin.inbox import router as admin_inbox_router

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
app.include_router(admin_feature_flags_router)
app.include_router(admin_notifications_router)
app.include_router(admin_inbox_router)

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
@app.get("/v1/admin/pharmacies")
async def list_pharmacies(user: User = Depends(require_admin)):
    return {"pharmacies": pharmacy_service.list_pharmacies()}


@app.get("/v1/admin/pharmacies/{pharmacy_id}")
async def get_pharmacy(pharmacy_id: str, user: User = Depends(require_admin)):
    p = pharmacy_service.get_pharmacy(pharmacy_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    return p


@app.post("/v1/admin/pharmacies")
async def create_pharmacy(request: Request, user: User = Depends(require_admin)):
    data = await request.json()
    if not data.get("name"):
        raise HTTPException(status_code=400, detail="Name required")
    return pharmacy_service.create_pharmacy(data)


@app.put("/v1/admin/pharmacies/{pharmacy_id}")
async def update_pharmacy(pharmacy_id: str, request: Request, user: User = Depends(require_admin)):
    data = await request.json()
    result = pharmacy_service.update_pharmacy(pharmacy_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    return result


@app.delete("/v1/admin/pharmacies/{pharmacy_id}")
async def delete_pharmacy(pharmacy_id: str, user: User = Depends(require_admin)):
    pharmacy_service.delete_pharmacy(pharmacy_id)
    return {"success": True}


@app.get("/v1/admin/whatsapp")
async def list_all_whatsapp(user: User = Depends(require_admin)):
    return {"numbers": pharmacy_service.list_whatsapp_numbers()}


@app.get("/v1/admin/pharmacies/{pharmacy_id}/whatsapp")
async def list_pharmacy_whatsapp(pharmacy_id: str, user: User = Depends(require_admin)):
    return {"numbers": pharmacy_service.list_whatsapp_numbers(pharmacy_id)}


@app.post("/v1/admin/pharmacies/{pharmacy_id}/whatsapp")
async def add_whatsapp(pharmacy_id: str, request: Request, user: User = Depends(require_admin)):
    data = await request.json()
    if not data.get("phone_number"):
        raise HTTPException(status_code=400, detail="Phone required")
    return pharmacy_service.add_whatsapp_number(pharmacy_id, data)


@app.put("/v1/admin/whatsapp/{number_id}")
async def update_whatsapp(number_id: str, request: Request, user: User = Depends(require_admin)):
    data = await request.json()
    result = pharmacy_service.update_whatsapp_number(number_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Number not found")
    return result


@app.delete("/v1/admin/whatsapp/{number_id}")
async def delete_whatsapp(number_id: str, user: User = Depends(require_admin)):
    pharmacy_service.delete_whatsapp_number(number_id)
    return {"success": True}



# ═══════════════════════════════════════════════════════════
# WHATSAPP SERVICE BRIDGE
# ═══════════════════════════════════════════════════════════
@app.put("/v1/admin/whatsapp/{phone}/connect")
async def whatsapp_mark_connected(phone: str, data: dict = None):
    """يُستدعى من Node.js عند اتصال WhatsApp."""
    try:
        from db import SessionLocal
        from sqlalchemy import text
        s = SessionLocal()
        try:
            # سجل الاتصال (اختياري — يعتمد على وجود جدول whatsapp_numbers)
            try:
                s.execute(text("""
                    INSERT INTO whatsapp_numbers (phone_number, status, connected_at)
                    VALUES (:p, 'connected', now())
                    ON CONFLICT (phone_number) DO UPDATE 
                    SET status = 'connected', connected_at = now()
                """), {"p": phone})
                s.commit()
            except Exception:
                s.rollback()
            return {"success": True, "phone": phone, "status": "connected"}
        finally:
            s.close()
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


@app.get("/v1/admin/whatsapp-service/health")
async def whatsapp_service_health(user: User = Depends(require_admin)):
    """Check WhatsApp service health."""
    return await whatsapp_bridge.health()


@app.get("/v1/admin/whatsapp-service/sessions")
async def whatsapp_service_sessions(user: User = Depends(require_admin)):
    """List all WhatsApp sessions."""
    sessions = await whatsapp_bridge.list_sessions()
    return {"sessions": sessions}


@app.post("/v1/admin/whatsapp-service/sessions")
async def whatsapp_service_create(
    request: Request,
    user: User = Depends(require_admin),
):
    """Create a new WhatsApp session (generates QR)."""
    data = await request.json()
    phone = data.get("phone_number")
    pharmacy_id = data.get("pharmacy_id")
    
    if not phone:
        raise HTTPException(status_code=400, detail="phone_number required")
    
    result = await whatsapp_bridge.create_session(phone, pharmacy_id)
    return result


@app.get("/v1/admin/whatsapp-service/sessions/{phone}/qr")
async def whatsapp_service_get_qr(
    phone: str,
    user: User = Depends(require_admin),
):
    """Get QR code for a session."""
    return await whatsapp_bridge.get_qr(phone)


@app.delete("/v1/admin/whatsapp-service/sessions/{phone}")
async def whatsapp_service_delete(
    phone: str,
    user: User = Depends(require_admin),
):
    """Delete a WhatsApp session."""
    return await whatsapp_bridge.delete_session(phone)


@app.post("/v1/admin/whatsapp-service/send")
async def whatsapp_service_send(
    request: Request,
    user: User = Depends(require_admin),
):
    """Send a test message."""
    data = await request.json()
    return await whatsapp_bridge.send_message(
        data.get("phone_number"),
        data.get("to"),
        data.get("message"),
    )



# ═══════════════════════════════════════════════════════════
# PUBLIC SELF-SERVICE ONBOARDING
# ═══════════════════════════════════════════════════════════
import secrets

_public_static = _Path(__file__).parent / "public" / "static"
if _public_static.exists():
    app.mount("/public/static", StaticFiles(directory=str(_public_static)), name="public_static")

    @app.get("/connect")
    async def _public_connect():
        """Public onboarding page."""
        return FileResponse(str(_public_static / "connect.html"))


@app.post("/v1/public/register")
async def public_register(request: Request):
    """Public self-service registration for pharmacies."""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    name = (data.get("pharmacy_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    
    # Validate
    if not name:
        raise HTTPException(status_code=400, detail="اسم الصيدلية مطلوب")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="بريد إلكتروني غير صحيح")
    if not phone:
        raise HTTPException(status_code=400, detail="رقم WhatsApp مطلوب")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="كلمة المرور 8 أحرف على الأقل")
    
    # Generate unique username from email
    username = email.split("@")[0]
    
    from sqlalchemy import text
    from db import SessionLocal
    from auth.jwt_handler import hash_password
    from uuid import uuid4
    
    db = SessionLocal()
    try:
        # Check if email exists
        existing = db.execute(text("""
            SELECT id FROM users WHERE email = :email OR username = :username
        """), {"email": email, "username": username}).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="الإيميل مسجل مسبقاً")
        
        # Create user
        user_id = str(uuid4())
        hashed = hash_password(password)
        
        db.execute(text("""
            INSERT INTO users (id, username, email, phone, full_name, role, hashed_password, is_active, is_verified)
            VALUES (:id, :username, :email, :phone, :full_name, 'admin', :hashed, TRUE, FALSE)
        """), {
            "id": user_id,
            "username": username,
            "email": email,
            "phone": phone,
            "full_name": name,
            "hashed": hashed,
        })
        
        # Create pharmacy
        pharmacy_id = str(uuid4())
        db.execute(text("""
            INSERT INTO pharmacies (id, name, name_ar, owner_id, phone, email, is_active)
            VALUES (:id, :name, :name_ar, :owner, :phone, :email, TRUE)
        """), {
            "id": pharmacy_id,
            "name": name,
            "name_ar": name,
            "owner": user_id,
            "phone": phone,
            "email": email,
        })
        
        # Create WhatsApp number record
        number_id = str(uuid4())
        db.execute(text("""
            INSERT INTO whatsapp_numbers (id, pharmacy_id, phone_number, display_name, mode, is_active, is_primary)
            VALUES (:id, :pid, :phone, :name, 'qr', FALSE, TRUE)
        """), {
            "id": number_id,
            "pid": pharmacy_id,
            "phone": phone,
            "name": f"الرقم الرئيسي - {name}",
        })
        
        db.commit()
        
        logger.info("public.registration", pharmacy=name, email=email, phone=phone)
        
        # Start WhatsApp session
        session_id = phone  # Use phone as session ID
        try:
            await whatsapp_bridge.create_session(phone, pharmacy_id)
        except Exception as e:
            logger.warning("whatsapp.session_create_failed", error=str(e)[:200])
        
        return {
            "success": True,
            "pharmacy_id": pharmacy_id,
            "pharmacy_name": name,
            "email": email,
            "phone": phone,
            "session_id": session_id,
            "message": "✅ تم إنشاء الحساب. امسح QR لربط WhatsApp",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("public.register_failed", error=str(e)[:200])
        raise HTTPException(status_code=500, detail=f"خطأ: {str(e)[:100]}")
    finally:
        db.close()


@app.get("/v1/public/qr/{session_id}")
async def public_get_qr(session_id: str):
    """Get QR code for a public session (no auth)."""
    try:
        # URL decode session_id
        import urllib.parse
        session_id = urllib.parse.unquote(session_id)
        
        data = await whatsapp_bridge.get_qr(session_id)
        return data
    except Exception as e:
        logger.error("public.qr_failed", error=str(e)[:200])
        return {"status": "error", "error": str(e)[:100]}


@app.get("/v1/public/status/{session_id}")
async def public_get_status(session_id: str):
    """Get connection status for a public session (no auth)."""
    try:
        import urllib.parse
        session_id = urllib.parse.unquote(session_id)
        
        # Get sessions list
        sessions = await whatsapp_bridge.list_sessions()
        
        # Find our session
        session_data = None
        for s in sessions:
            if s.get("phone_number") == session_id:
                session_data = s
                break
        
        if not session_data:
            return {"status": "initializing"}
        
        status = session_data.get("status", "unknown")
        
        # Get pharmacy info if connected
        pharmacy_name = ""
        email = ""
        if status == "connected":
            from sqlalchemy import text
            from db import SessionLocal
            db = SessionLocal()
            try:
                result = db.execute(text("""
                    SELECT p.name_ar, p.email FROM pharmacies p
                    JOIN whatsapp_numbers w ON w.pharmacy_id = p.id
                    WHERE w.phone_number = :phone
                """), {"phone": session_id}).first()
                if result:
                    pharmacy_name = result[0] or ""
                    email = result[1] or ""
            finally:
                db.close()
        
        return {
            "status": status,
            "phone_number": session_id,
            "pharmacy_name": pharmacy_name,
            "email": email,
        }
    except Exception as e:
        logger.error("public.status_failed", error=str(e)[:200])
        return {"status": "error", "error": str(e)[:100]}



# ═══════════════════════════════════════════════════════════
# WHATSAPP INCOMING WEBHOOK (X-API-Key auth)
# ═══════════════════════════════════════════════════════════
@app.post("/v1/whatsapp/incoming")
async def whatsapp_incoming(
    request: Request,
):
    """Receive incoming WhatsApp message from WhatsApp bridge.
    
    Auth: X-API-Key header (not Bearer token)
    """
    # Verify API key
    api_key = request.headers.get("X-API-Key", "")
    expected = settings.webhook_api_key
    
    if not api_key or api_key != expected:
        logger.warning("whatsapp.incoming_unauthorized", has_key=bool(api_key))
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or "whatsapp"
    pharmacy_phone = data.get("pharmacy_phone") or ""
    
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    # Find pharmacy by phone
    from sqlalchemy import text
    from db import SessionLocal
    
    user_role = "customer"
    pharmacy_id = None
    
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT pharmacy_id::text FROM whatsapp_numbers
            WHERE phone_number = :phone AND is_active = TRUE
            LIMIT 1
        """), {"phone": pharmacy_phone}).first()
        
        if result:
            pharmacy_id = result[0]
    finally:
        db.close()
    
    logger.info(
        "whatsapp.incoming",
        phone=pharmacy_phone,
        message=message[:50],
        pharmacy_id=pharmacy_id,
    )
    
    # Call orchestrator
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: orchestrator.handle(message, user_role=user_role),
    )
    
    response_text = result.response.text or "عذراً، لم أفهم رسالتك."
    
    # Save session
    session = session_store.get(session_id) or {
        "user_id": "whatsapp",
        "messages": [],
    }
    session["messages"].append({"role": "user", "content": message})
    session["messages"].append({"role": "agent", "content": response_text})
    session_store.set(session_id, session)
    
    # Save message to DB if pharmacy found
    if pharmacy_id:
        try:
            db = SessionLocal()
            try:
                from uuid import uuid4
                db.execute(text("""
                    INSERT INTO messages 
                        (id, pharmacy_id, from_phone, content, direction, 
                         processed, chatbot_response, handler, received_at, created_at, updated_at)
                    VALUES 
                        (:id, :pid, :from_phone, :content, 'inbound',
                         TRUE, :response, :handler, NOW(), NOW(), NOW())
                """), {
                    "id": str(uuid4()),
                    "pid": pharmacy_id,
                    "from_phone": session_id.split(":")[-1] if ":" in session_id else "unknown",
                    "content": message,
                    "response": response_text,
                    "handler": result.handler,
                })
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning("whatsapp.save_message_failed", error=str(e)[:200])
    
    # ═══ Broadcast to Live Feed ═══
    try:
        await live_feed.broadcast({
            "type": "whatsapp_message",
            "phone": pharmacy_phone,
            "from": session_id.split(":")[-1] if ":" in session_id else session_id,
            "session_id": session_id,
            "message": message,
            "response": response_text,
            "handler": result.handler,
            "confidence": result.response.confidence,
            "needs_human": result.response.needs_human,
            "action": result.response.action,
            "pharmacy_id": pharmacy_id,
        })
    except Exception as e:
        logger.warning("live_feed.broadcast_failed", error=str(e)[:200])
    
    return {
        "success": True,
        "response": response_text,
        "handler": result.handler,
        "confidence": result.response.confidence,
        "needs_human": result.response.needs_human,
        "action": result.response.action,
        "pharmacy_id": pharmacy_id,
        "session_id": session_id,
    }



# ═══════════════════════════════════════════════════════════
# WHATSAPP SESSION LIFECYCLE
# ═══════════════════════════════════════════════════════════
@app.post("/v1/admin/whatsapp-service/sessions/{phone}/disconnect")
async def whatsapp_disconnect_session(
    phone: str,
    user: User = Depends(require_admin),
):
    """Disconnect WhatsApp session (keeps DB record as suspended)."""
    import urllib.parse
    phone = urllib.parse.unquote(phone)
    
    # Disconnect from WhatsApp service
    result = await whatsapp_bridge.disconnect_session(phone)
    
    # Update DB
    from sqlalchemy import text
    from db import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE whatsapp_numbers
            SET status = 'suspended', is_active = FALSE, disconnected_at = NOW(), updated_at = NOW()
            WHERE phone_number = :phone
        """), {"phone": phone})
        db.commit()
        logger.info("whatsapp.suspended", phone=phone)
    finally:
        db.close()
    
    return {"success": True, "action": "suspended", "phone": phone}


@app.post("/v1/admin/whatsapp-service/sessions/{phone}/activate")
async def whatsapp_activate_session(
    phone: str,
    user: User = Depends(require_admin),
):
    """Reactivate a suspended session (create new QR)."""
    import urllib.parse
    phone = urllib.parse.unquote(phone)
    
    from sqlalchemy import text
    from db import SessionLocal
    db = SessionLocal()
    try:
        # Get pharmacy_id
        result = db.execute(text("""
            SELECT pharmacy_id::text FROM whatsapp_numbers WHERE phone_number = :phone
        """), {"phone": phone}).first()
        
        pharmacy_id = result[0] if result else None
        
        # Create new session
        session_result = await whatsapp_bridge.create_session(phone, pharmacy_id)
        
        # Update DB
        db.execute(text("""
            UPDATE whatsapp_numbers
            SET status = 'pending', is_active = TRUE, updated_at = NOW()
            WHERE phone_number = :phone
        """), {"phone": phone})
        db.commit()
        
        logger.info("whatsapp.activated", phone=phone)
        return {"success": True, "action": "activated", "phone": phone, "session": session_result}
    finally:
        db.close()


@app.delete("/v1/admin/whatsapp-service/sessions/{phone}/delete-all")
async def whatsapp_delete_completely(
    phone: str,
    user: User = Depends(require_admin),
):
    """Delete session completely: disconnect + remove files + delete DB record."""
    import urllib.parse
    phone = urllib.parse.unquote(phone)
    
    # 1. Delete from WhatsApp service
    delete_result = await whatsapp_bridge.delete_session(phone)
    
    # 2. Delete from DB
    from sqlalchemy import text
    from db import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("""
            DELETE FROM whatsapp_numbers WHERE phone_number = :phone
        """), {"phone": phone})
        db.commit()
        logger.info("whatsapp.deleted", phone=phone)
    finally:
        db.close()
    
    return {"success": True, "action": "deleted", "phone": phone}



# ═══════════════════════════════════════════════════════════
# LIVE FEED (SSE)
# ═══════════════════════════════════════════════════════════
@app.get("/v1/admin/live-feed")
async def live_feed_stream(request: Request):
    """Server-Sent Events stream for real-time messages.
    
    Streams all incoming WhatsApp messages to connected admin dashboards.
    """
    from fastapi.responses import StreamingResponse
    
    async def event_generator():
        async for event in live_feed.subscribe():
            if await request.is_disconnected():
                break
            yield event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/v1/admin/live-feed/stats")
async def live_feed_stats(user: User = Depends(require_admin)):
    """Get live feed statistics."""
    return live_feed.stats()


@app.post("/v1/admin/live-feed/test")
async def live_feed_test(user: User = Depends(require_admin)):
    """Send a test event to live feed."""
    await live_feed.broadcast({
        "type": "test",
        "message": "🔔 اختبار البث الحي",
        "from": "system",
    })
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# PHARMACY HARD DELETE
# ═══════════════════════════════════════════════════════════
@app.delete("/v1/admin/pharmacies/{pharmacy_id}/hard")
async def hard_delete_pharmacy(
    pharmacy_id: str,
    user: User = Depends(require_admin),
):
    """Hard delete pharmacy + all related data (irreversible)."""
    from sqlalchemy import text
    from db import SessionLocal
    
    db = SessionLocal()
    try:
        # Delete related WhatsApp sessions first
        numbers = db.execute(text("""
            SELECT phone_number FROM whatsapp_numbers WHERE pharmacy_id = :pid
        """), {"pid": pharmacy_id}).fetchall()
        
        for row in numbers:
            phone = row[0]
            try:
                await whatsapp_bridge.delete_session(phone)
            except Exception:
                pass
        
        # Cascade delete (FK ON DELETE CASCADE handles related tables)
        result = db.execute(text("""
            DELETE FROM pharmacies WHERE id = :pid
        """), {"pid": pharmacy_id})
        db.commit()
        
        deleted = result.rowcount > 0
        
        if deleted:
            logger.info("pharmacy.hard_deleted", pharmacy_id=pharmacy_id)
            return {"success": True, "deleted": True, "pharmacy_id": pharmacy_id}
        else:
            raise HTTPException(status_code=404, detail="Pharmacy not found")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("pharmacy.hard_delete_failed", error=str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:100])
    finally:
        db.close()




# ═══════════════════════════════════════════════════════════
# PHARMACY HARD DELETE
# ═══════════════════════════════════════════════════════════
@app.delete("/v1/admin/pharmacies/{pharmacy_id}/hard-delete")
async def pharmacy_hard_delete(
    pharmacy_id: str,
    user: User = Depends(require_admin),
):
    """Hard delete pharmacy + all related data.
    
    This will:
    - Disconnect all WhatsApp sessions
    - Delete all related DB records (cascade)
    - Cannot be undone
    """
    from sqlalchemy import text
    from db import SessionLocal
    
    # 1. Get WhatsApp numbers before deletion
    db = SessionLocal()
    try:
        numbers = db.execute(text("""
            SELECT phone_number FROM whatsapp_numbers WHERE pharmacy_id = :pid
        """), {"pid": pharmacy_id}).fetchall()
    finally:
        db.close()
    
    # 2. Disconnect all WhatsApp sessions
    disconnected = 0
    for row in numbers:
        phone = row[0]
        try:
            result = await whatsapp_bridge.delete_session(phone)
            if result.get("success"):
                disconnected += 1
        except Exception as e:
            logger.warning("whatsapp.delete_failed", phone=phone, error=str(e)[:100])
    
    # 3. Delete pharmacy (CASCADE will delete related)
    db = SessionLocal()
    try:
        result = db.execute(text("""
            DELETE FROM pharmacies WHERE id = :pid
        """), {"pid": pharmacy_id})
        db.commit()
        
        deleted = result.rowcount > 0
        logger.info(
            "pharmacy.hard_deleted",
            pharmacy_id=pharmacy_id,
            sessions_disconnected=disconnected,
        )
        
        return {
            "success": True,
            "pharmacy_id": pharmacy_id,
            "deleted": deleted,
            "sessions_disconnected": disconnected,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# PHARMACY SUSPEND (Soft delete)
# ═══════════════════════════════════════════════════════════
@app.post("/v1/admin/pharmacies/{pharmacy_id}/suspend")
async def pharmacy_suspend(
    pharmacy_id: str,
    user: User = Depends(require_admin),
):
    """Suspend pharmacy — disable but keep data."""
    from sqlalchemy import text
    from db import SessionLocal
    
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE pharmacies 
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = :pid
        """), {"pid": pharmacy_id})
        db.commit()
        
        logger.info("pharmacy.suspended", pharmacy_id=pharmacy_id)
        return {"success": True, "action": "suspended", "pharmacy_id": pharmacy_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# PHARMACY ACTIVATE
# ═══════════════════════════════════════════════════════════
@app.post("/v1/admin/pharmacies/{pharmacy_id}/activate")
async def pharmacy_activate(
    pharmacy_id: str,
    user: User = Depends(require_admin),
):
    """Reactivate suspended pharmacy."""
    from sqlalchemy import text
    from db import SessionLocal
    
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE pharmacies 
            SET is_active = TRUE, updated_at = NOW()
            WHERE id = :pid
        """), {"pid": pharmacy_id})
        db.commit()
        
        logger.info("pharmacy.activated", pharmacy_id=pharmacy_id)
        return {"success": True, "action": "activated", "pharmacy_id": pharmacy_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# PHARMACY UPDATE (full edit)
# ═══════════════════════════════════════════════════════════
@app.put("/v1/admin/pharmacies/{pharmacy_id}/full-update")
async def pharmacy_full_update(
    pharmacy_id: str,
    request: Request,
    user: User = Depends(require_admin),
):
    """Full update of pharmacy data."""
    from sqlalchemy import text
    from db import SessionLocal
    
    data = await request.json()
    
    # Allowed fields
    allowed = ["name", "name_ar", "phone", "email", "address", "city", "subscription_plan"]
    updates = {k: v for k, v in data.items() if k in allowed}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    db = SessionLocal()
    try:
        # ✅ Whitelist
        ALLOWED_COLS = {
            "name", "name_ar", "phone", "email", "address",
            "city", "governorate", "latitude", "longitude",
            "is_active", "subscription_status", "notes"
        }
        updates = {k: v for k, v in updates.items() if k in ALLOWED_COLS}
        
        if not updates:
            return {"success": False, "error": "No valid fields"}
        
        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["pid"] = pharmacy_id
        
        result = db.execute(text(f"""
            UPDATE pharmacies 
            SET {set_clause}, updated_at = NOW()
            WHERE id = :pid
        """), updates)
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pharmacy not found")
        
        # Get updated pharmacy
        ph = db.execute(text("""
            SELECT id::text, name, name_ar, phone, email, address, city,
                   subscription_plan, is_active, created_at, updated_at
            FROM pharmacies WHERE id = :pid
        """), {"pid": pharmacy_id}).first()
        
        logger.info("pharmacy.updated", pharmacy_id=pharmacy_id, fields=list(updates.keys()))
        
        return {"success": True, "pharmacy": dict(ph._mapping) if ph else None}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()



# ═══════════════════════════════════════════════════════════
# PRIVACY POLICY + TERMS
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# DATABASE EXPANSION ENDPOINTS
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# FEATURE FLAGS CRUD
# ═══════════════════════════════════════════════════════════
@app.put("/v1/admin/feature-flags/{flag_key}")
async def update_feature_flag(flag_key: str, request: Request, user: User = Depends(require_admin)):
    from sqlalchemy import text
    from db import SessionLocal
    
    data = await request.json()
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE feature_flags 
            SET is_enabled = COALESCE(:enabled, is_enabled),
                rollout_percentage = COALESCE(:rollout, rollout_percentage),
                updated_at = NOW()
            WHERE key = :key
        """), {
            "key": flag_key,
            "enabled": data.get("is_enabled"),
            "rollout": data.get("rollout_percentage"),
        })
        db.commit()
        return {"success": True, "key": flag_key}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# ALERTS CRUD
# ═══════════════════════════════════════════════════════════
@app.post("/v1/admin/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: User = Depends(require_admin)):
    from sqlalchemy import text
    from db import SessionLocal
    
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE alerts 
            SET is_resolved = TRUE, resolved_at = NOW(), resolved_by = :uid
            WHERE id = :id
        """), {"id": alert_id, "uid": user.id})
        db.commit()
        return {"success": True}
    finally:
        db.close()


@app.post("/v1/admin/alerts")
async def create_alert(request: Request, user: User = Depends(require_admin)):
    from sqlalchemy import text
    from db import SessionLocal
    from uuid import uuid4
    
    data = await request.json()
    db = SessionLocal()
    try:
        aid = str(uuid4())
        db.execute(text("""
            INSERT INTO alerts (id, pharmacy_id, type, severity, title, message)
            VALUES (:id, :pid, :type, :sev, :title, :msg)
        """), {
            "id": aid,
            "pid": data.get("pharmacy_id"),
            "type": data.get("type", "info"),
            "sev": data.get("severity", "info"),
            "title": data.get("title", ""),
            "msg": data.get("message", ""),
        })
        db.commit()
        return {"success": True, "id": aid}
    finally:
        db.close()


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
