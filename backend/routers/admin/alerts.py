"""Admin alerts routes — /v1/admin/alerts."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_admin
from db import SessionLocal

router = APIRouter(prefix="/v1/admin/alerts", tags=["admin-alerts"])


@router.get("")
async def list_alerts(
    unresolved_only: bool = True,
    user: User = Depends(require_admin),
):
    """List system alerts."""
    db = SessionLocal()
    try:
        where = "WHERE a.is_resolved = FALSE" if unresolved_only else ""
        result = db.execute(text(f"""
            SELECT a.id::text, a.type, a.severity, a.title, a.message,
                   a.is_resolved, a.created_at,
                   p.name_ar AS pharmacy_name
            FROM alerts a
            LEFT JOIN pharmacies p ON p.id = a.pharmacy_id
            {where}
            ORDER BY a.created_at DESC
            LIMIT 100
        """))
        return {"alerts": [dict(row._mapping) for row in result]}
    finally:
        db.close()


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE alerts SET is_resolved = TRUE, resolved_at = NOW()
            WHERE id = :id
        """), {"id": alert_id})
        db.commit()
        return {"success": True}
    finally:
        db.close()


@router.post("")
async def create_alert(request: Request, user: User = Depends(require_admin)):
    from uuid import uuid4
    data = await request.json()
    db = SessionLocal()
    try:
        aid = str(uuid4())
        db.execute(text("""
            INSERT INTO alerts (id, type, severity, title, message, pharmacy_id)
            VALUES (:id, :type, :sev, :title, :msg, :pid)
        """), {
            "id": aid,
            "type": data.get("type", "info"),
            "sev": data.get("severity", "low"),
            "title": data.get("title", ""),
            "msg": data.get("message", ""),
            "pid": data.get("pharmacy_id"),
        })
        db.commit()
        return {"success": True, "id": aid}
    finally:
        db.close()
