"""Admin subscriptions routes — /v1/admin/subscriptions."""
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_admin
from db import SessionLocal

router = APIRouter(prefix="/v1/admin/subscriptions", tags=["admin-subscriptions"])


@router.get("")
async def list_subscriptions(user: User = Depends(require_admin)):
    """List all subscriptions."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT s.id::text, s.pharmacy_id::text, p.name_ar AS pharmacy_name,
                   s.plan, s.status, s.price_monthly, s.currency,
                   s.started_at, s.expires_at, s.auto_renew
            FROM subscriptions s
            LEFT JOIN pharmacies p ON p.id = s.pharmacy_id
            ORDER BY s.created_at DESC
        """))
        return {"subscriptions": [dict(row._mapping) for row in result]}
    finally:
        db.close()


@router.post("")
async def create_subscription(request: Request, user: User = Depends(require_admin)):
    data = await request.json()
    db = SessionLocal()
    try:
        sid = str(uuid4())
        db.execute(text("""
            INSERT INTO subscriptions (id, pharmacy_id, plan, status, price_monthly, expires_at)
            VALUES (:id, :pid, :plan, 'active', :price, NOW() + INTERVAL '1 year')
        """), {
            "id": sid,
            "pid": data.get("pharmacy_id"),
            "plan": data.get("plan", "basic"),
            "price": data.get("price_monthly", 0),
        })
        db.commit()
        return {"success": True, "id": sid}
    finally:
        db.close()


@router.put("/{sub_id}")
async def update_subscription(sub_id: str, request: Request, user: User = Depends(require_admin)):
    data = await request.json()
    allowed = ["plan", "status", "price_monthly", "auto_renew", "expires_at"]
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return {"success": True}

    db = SessionLocal()
    try:
        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["sid"] = sub_id
        db.execute(text(f"""
            UPDATE subscriptions SET {set_clause}, updated_at = NOW() WHERE id = :sid
        """), updates)
        db.commit()
        return {"success": True}
    finally:
        db.close()
