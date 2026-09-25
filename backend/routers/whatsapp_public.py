"""Public WhatsApp routes — /v1/public/* + /v1/whatsapp/incoming."""
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import text

from config import settings
from auth.jwt_handler import hash_password
from core.orchestrator import orchestrator
from session.session_store import session_store
from services.whatsapp_bridge import whatsapp_bridge
from services.live_feed import live_feed
from db import SessionLocal
import structlog

logger = structlog.get_logger()
router = APIRouter(tags=["whatsapp-public"])


# ═══════════════════════════════════════════════════════════
#  PUBLIC STATIC PAGE
# ═══════════════════════════════════════════════════════════
_public_static = Path(__file__).parent.parent / "public" / "static"


@router.get("/connect")
async def public_connect():
    """Public onboarding page."""
    if not _public_static.exists():
        raise HTTPException(404, "Page not found")
    return FileResponse(str(_public_static / "connect.html"))


# ═══════════════════════════════════════════════════════════
#  PUBLIC REGISTRATION
# ═══════════════════════════════════════════════════════════
@router.post("/v1/public/register")
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

    username = email.split("@")[0]

    db = SessionLocal()
    try:
        existing = db.execute(text("""
            SELECT id FROM users WHERE email = :email OR username = :username
        """), {"email": email, "username": username}).first()

        if existing:
            raise HTTPException(status_code=400, detail="الإيميل مسجل مسبقاً")

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

        session_id = phone
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


# ═══════════════════════════════════════════════════════════
#  PUBLIC QR + STATUS (no auth)
# ═══════════════════════════════════════════════════════════
@router.get("/v1/public/qr/{session_id}")
async def public_get_qr(session_id: str):
    """Get QR code for a public session (no auth)."""
    try:
        import urllib.parse
        session_id = urllib.parse.unquote(session_id)
        data = await whatsapp_bridge.get_qr(session_id)
        return data
    except Exception as e:
        logger.error("public.qr_failed", error=str(e)[:200])
        return {"status": "error", "error": str(e)[:100]}


@router.get("/v1/public/status/{session_id}")
async def public_get_status(session_id: str):
    """Get connection status for a public session (no auth)."""
    try:
        import urllib.parse
        session_id = urllib.parse.unquote(session_id)

        sessions = await whatsapp_bridge.list_sessions()

        session_data = None
        for s in sessions:
            if s.get("phone_number") == session_id:
                session_data = s
                break

        if not session_data:
            return {"status": "initializing"}

        status = session_data.get("status", "unknown")

        pharmacy_name = ""
        email = ""
        if status == "connected":
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
#  WHATSAPP INCOMING WEBHOOK (X-API-Key auth)
# ═══════════════════════════════════════════════════════════
@router.post("/v1/whatsapp/incoming")
async def whatsapp_incoming(request: Request):
    """Receive incoming WhatsApp message from WhatsApp bridge.

    Auth: X-API-Key header (not Bearer token)
    """
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

    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: orchestrator.handle(message, user_role=user_role),
    )

    response_text = result.response.text or "عذراً، لم أفهم رسالتك."

    session = session_store.get(session_id) or {"user_id": "whatsapp", "messages": []}
    session["messages"].append({"role": "user", "content": message})
    session["messages"].append({"role": "agent", "content": response_text})
    session_store.set(session_id, session)

    if pharmacy_id:
        try:
            db = SessionLocal()
            try:
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
