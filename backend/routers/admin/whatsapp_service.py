"""Admin WhatsApp Service routes — /v1/admin/whatsapp-service/* + /connect."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_admin
from services.whatsapp_bridge import whatsapp_bridge
from db import SessionLocal
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin", tags=["admin-whatsapp-service"])


# ═══════════════════════════════════════════════════════════
#  CALLBACK FROM NODE.JS (no auth — X-API-Key if needed)
# ═══════════════════════════════════════════════════════════
@router.put("/whatsapp/{phone}/connect")
async def whatsapp_mark_connected(phone: str, data: dict = None):
    """يُستدعى من Node.js عند اتصال WhatsApp."""
    db = SessionLocal()
    try:
        try:
            db.execute(text("""
                INSERT INTO whatsapp_numbers (phone_number, status, connected_at)
                VALUES (:p, 'connected', now())
                ON CONFLICT (phone_number) DO UPDATE
                SET status = 'connected', connected_at = now()
            """), {"p": phone})
            db.commit()
        except Exception:
            db.rollback()
        return {"success": True, "phone": phone, "status": "connected"}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  HEALTH + SESSIONS
# ═══════════════════════════════════════════════════════════
@router.get("/whatsapp-service/health")
async def whatsapp_service_health(user: User = Depends(require_admin)):
    """Check WhatsApp service health."""
    return await whatsapp_bridge.health()


@router.get("/whatsapp-service/sessions")
async def whatsapp_service_sessions(user: User = Depends(require_admin)):
    """List all WhatsApp sessions."""
    sessions = await whatsapp_bridge.list_sessions()
    return {"sessions": sessions}


@router.post("/whatsapp-service/sessions")
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

    return await whatsapp_bridge.create_session(phone, pharmacy_id)


@router.get("/whatsapp-service/sessions/{phone}/qr")
async def whatsapp_service_get_qr(
    phone: str,
    user: User = Depends(require_admin),
):
    """Get QR code for a session."""
    return await whatsapp_bridge.get_qr(phone)


@router.delete("/whatsapp-service/sessions/{phone}")
async def whatsapp_service_delete(
    phone: str,
    user: User = Depends(require_admin),
):
    """Delete a WhatsApp session."""
    return await whatsapp_bridge.delete_session(phone)


@router.post("/whatsapp-service/send")
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
#  DISCONNECT / ACTIVATE / DELETE-ALL
# ═══════════════════════════════════════════════════════════
@router.post("/whatsapp-service/sessions/{phone}/disconnect")
async def whatsapp_disconnect_session(
    phone: str,
    user: User = Depends(require_admin),
):
    """Disconnect (suspend) a WhatsApp session."""
    import urllib.parse
    phone = urllib.parse.unquote(phone)

    await whatsapp_bridge.disconnect_session(phone)

    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE whatsapp_numbers
            SET status = 'suspended', is_active = FALSE, updated_at = NOW()
            WHERE phone_number = :phone
        """), {"phone": phone})
        db.commit()
    finally:
        db.close()

    return {"success": True, "action": "suspended", "phone": phone}


@router.post("/whatsapp-service/sessions/{phone}/activate")
async def whatsapp_activate_session(
    phone: str,
    user: User = Depends(require_admin),
):
    """Reactivate a suspended session."""
    import urllib.parse
    phone = urllib.parse.unquote(phone)

    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT pharmacy_id::text FROM whatsapp_numbers WHERE phone_number = :phone
        """), {"phone": phone}).first()

        pharmacy_id = result[0] if result else None
        session_result = await whatsapp_bridge.create_session(phone, pharmacy_id)

        db.execute(text("""
            UPDATE whatsapp_numbers
            SET status = 'pending', is_active = TRUE, updated_at = NOW()
            WHERE phone_number = :phone
        """), {"phone": phone})
        db.commit()

        return {"success": True, "action": "activated", "phone": phone, "session": session_result}
    finally:
        db.close()


@router.delete("/whatsapp-service/sessions/{phone}/delete-all")
async def whatsapp_delete_completely(
    phone: str,
    user: User = Depends(require_admin),
):
    """Delete session completely: disconnect + remove files + delete DB record."""
    import urllib.parse
    phone = urllib.parse.unquote(phone)

    await whatsapp_bridge.delete_session(phone)

    db = SessionLocal()
    try:
        db.execute(text("""
            DELETE FROM whatsapp_numbers WHERE phone_number = :phone
        """), {"phone": phone})
        db.commit()
    finally:
        db.close()

    return {"success": True, "action": "deleted", "phone": phone}
