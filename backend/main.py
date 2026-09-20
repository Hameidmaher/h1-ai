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
from services.pharmacy_service import pharmacy_service
from services.whatsapp_bridge import whatsapp_bridge

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
from datetime import datetime

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
                        (:id, :pid, :from_phone, :content, 'incoming',
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

