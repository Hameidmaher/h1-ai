"""Admin notifications + usage-stats routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_admin
from db import SessionLocal

router = APIRouter(prefix="/v1/admin", tags=["admin-notifications"])


@router.get("/notifications")
async def list_notifications(
    limit: int = 50,
    user: User = Depends(require_admin),
):
    """List notifications."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT n.id::text, n.type, n.title, n.message, n.is_read,
                   n.priority, n.created_at
            FROM notifications n
            WHERE n.user_id = :uid OR n.pharmacy_id IS NULL
            ORDER BY n.created_at DESC
            LIMIT :limit
        """), {"uid": user.id, "limit": limit})
        return {"notifications": [dict(row._mapping) for row in result]}
    finally:
        db.close()


@router.get("/usage-stats")
async def list_usage_stats(
    days: int = 30,
    user: User = Depends(require_admin),
):
    """Get usage statistics."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT date,
                   SUM(messages_sent) AS messages_sent,
                   SUM(messages_received) AS messages_received,
                   SUM(ai_responses) AS ai_responses,
                   SUM(unique_customers) AS unique_customers
            FROM usage_stats
            WHERE date >= CURRENT_DATE - INTERVAL ':days days'
            GROUP BY date
            ORDER BY date DESC
        """), {"days": days})
        return {"stats": [dict(row._mapping) for row in result]}
    finally:
        db.close()
