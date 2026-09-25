"""Super Admin routes — /v1/super/* (multitenant management)."""
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_super_admin
from auth.jwt_handler import hash_password
from db import SessionLocal

router = APIRouter(prefix="/v1/super", tags=["super-admin"])


# ═══════════════════════════════════════════════════════════
#  Pydantic Models
# ═══════════════════════════════════════════════════════════
class PharmacyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    name_ar: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    subscription_plan: str = "basic"
    is_active: bool = True


class PharmacyUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    subscription_plan: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(customer|pharmacist|admin|super_admin)$")
    full_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    pharmacy_id: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    pharmacy_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════
#  PHARMACIES CRUD
# ═══════════════════════════════════════════════════════════
@router.get("/pharmacies")
async def list_pharmacies(
    is_active: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_super_admin),
):
    """List all pharmacies (Super Admin only)."""
    db = SessionLocal()
    try:
        q = "SELECT id, name, name_ar, phone, email, city, subscription_plan, is_active, subscription_expires_at, created_at FROM pharmacies WHERE 1=1"
        params = {}
        if is_active is not None:
            q += " AND is_active = :is_active"
            params["is_active"] = is_active
        q += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = db.execute(text(q), params)
        pharmacies = [dict(r._mapping) for r in result]
        return {"pharmacies": pharmacies, "count": len(pharmacies)}
    finally:
        db.close()


@router.get("/pharmacies/{pharmacy_id}")
async def get_pharmacy(
    pharmacy_id: str,
    user: User = Depends(require_super_admin),
):
    """Get one pharmacy."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, name_ar, owner_id, phone, email, address, city,
                   logo_url, subscription_plan, subscription_expires_at,
                   is_active, settings, created_at, updated_at
            FROM pharmacies WHERE id = :id
        """), {"id": pharmacy_id}).first()

        if not result:
            raise HTTPException(404, "الصيدلية غير موجودة")

        return dict(result._mapping)
    finally:
        db.close()


@router.post("/pharmacies")
async def create_pharmacy(
    data: PharmacyCreate,
    user: User = Depends(require_super_admin),
):
    """Create a new pharmacy."""
    db = SessionLocal()
    try:
        pid = str(uuid4())
        db.execute(text("""
            INSERT INTO pharmacies (id, name, name_ar, phone, email, address, city,
                                    subscription_plan, is_active)
            VALUES (:id, :name, :name_ar, :phone, :email, :address, :city,
                    :subscription_plan, :is_active)
        """), {
            "id": pid,
            "name": data.name,
            "name_ar": data.name_ar,
            "phone": data.phone,
            "email": data.email,
            "address": data.address,
            "city": data.city,
            "subscription_plan": data.subscription_plan,
            "is_active": data.is_active,
        })
        db.commit()
        return {"success": True, "id": pid}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"خطأ: {str(e)[:200]}")
    finally:
        db.close()


@router.put("/pharmacies/{pharmacy_id}")
async def update_pharmacy(
    pharmacy_id: str,
    data: PharmacyUpdate,
    user: User = Depends(require_super_admin),
):
    """Update pharmacy."""
    db = SessionLocal()
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return {"success": True}

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["pid"] = pharmacy_id

        db.execute(text(f"""
            UPDATE pharmacies SET {set_clause}, updated_at = NOW()
            WHERE id = :pid
        """), updates)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"خطأ: {str(e)[:200]}")
    finally:
        db.close()


@router.delete("/pharmacies/{pharmacy_id}")
async def delete_pharmacy(
    pharmacy_id: str,
    user: User = Depends(require_super_admin),
):
    """Soft delete pharmacy."""
    if pharmacy_id == "00000000-0000-0000-0000-000000000001":
        raise HTTPException(400, "لا يمكن حذف الصيدلية الافتراضية")

    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE pharmacies SET is_active = FALSE, updated_at = NOW()
            WHERE id = :id
        """), {"id": pharmacy_id})
        db.commit()
        return {"success": True}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  USERS CRUD
# ═══════════════════════════════════════════════════════════
@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    pharmacy_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_super_admin),
):
    """List all users."""
    db = SessionLocal()
    try:
        q = "SELECT id, username, email, phone, full_name, role, is_active, pharmacy_id, created_at FROM users WHERE 1=1"
        params = {}
        if role:
            q += " AND role = :role"
            params["role"] = role
        if pharmacy_id:
            q += " AND pharmacy_id = :pid"
            params["pid"] = pharmacy_id
        q += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = db.execute(text(q), params)
        users = [dict(r._mapping) for r in result]
        return {"users": users, "count": len(users)}
    finally:
        db.close()


@router.post("/users")
async def create_user(
    data: UserCreate,
    user: User = Depends(require_super_admin),
):
    """Create a new user."""
    db = SessionLocal()
    try:
        # تحقق من عدم التكرار
        existing = db.execute(
            text("SELECT 1 FROM users WHERE username = :u"),
            {"u": data.username}
        ).first()
        if existing:
            raise HTTPException(400, "اسم المستخدم موجود")

        uid = str(uuid4())
        db.execute(text("""
            INSERT INTO users (id, username, hashed_password, role, full_name,
                              email, phone, pharmacy_id, is_active)
            VALUES (:id, :username, :hash, :role, :full_name,
                    :email, :phone, :pharmacy_id, TRUE)
        """), {
            "id": uid,
            "username": data.username,
            "hash": hash_password(data.password),
            "role": data.role,
            "full_name": data.full_name,
            "email": data.email,
            "phone": data.phone,
            "pharmacy_id": data.pharmacy_id,
        })
        db.commit()
        return {"success": True, "id": uid}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"خطأ: {str(e)[:200]}")
    finally:
        db.close()


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    user: User = Depends(require_super_admin),
):
    """Update user."""
    db = SessionLocal()
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return {"success": True}

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["uid"] = user_id

        db.execute(text(f"""
            UPDATE users SET {set_clause}, updated_at = NOW()
            WHERE id = :uid
        """), updates)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"خطأ: {str(e)[:200]}")
    finally:
        db.close()


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    user: User = Depends(require_super_admin),
):
    """Delete user."""
    if user_id == user.id:
        raise HTTPException(400, "لا يمكن حذف حسابك")

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        db.commit()
        return {"success": True}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════
@router.get("/stats")
async def platform_stats(user: User = Depends(require_super_admin)):
    """Platform-wide statistics."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM pharmacies) AS total_pharmacies,
                (SELECT COUNT(*) FROM pharmacies WHERE is_active = TRUE) AS active_pharmacies,
                (SELECT COUNT(*) FROM users) AS total_users,
                (SELECT COUNT(*) FROM users WHERE role = 'admin') AS admins,
                (SELECT COUNT(*) FROM users WHERE role = 'pharmacist') AS pharmacists,
                (SELECT COUNT(*) FROM users WHERE role = 'customer') AS customers,
                (SELECT COUNT(*) FROM messages) AS total_messages,
                (SELECT COUNT(*) FROM messages WHERE received_at >= CURRENT_DATE) AS messages_today,
                (SELECT COUNT(*) FROM conversations) AS total_conversations,
                (SELECT COUNT(*) FROM conversations WHERE unread_count > 0) AS unread_conversations
        """))
        return dict(result.first()._mapping)
    finally:
        db.close()


@router.get("/pharmacies/{pharmacy_id}/stats")
async def pharmacy_stats(
    pharmacy_id: str,
    user: User = Depends(require_super_admin),
):
    """Per-pharmacy statistics."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM users WHERE pharmacy_id = :pid) AS users,
                (SELECT COUNT(*) FROM messages WHERE pharmacy_id = :pid) AS messages,
                (SELECT COUNT(*) FROM conversations WHERE pharmacy_id = :pid) AS conversations,
                (SELECT COUNT(*) FROM products WHERE pharmacy_id = :pid) AS products,
                (SELECT COUNT(*) FROM inventory WHERE pharmacy_id = :pid) AS inventory_items
        """), {"pid": pharmacy_id})
        return dict(result.first()._mapping)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  SUBSCRIPTIONS
# ═══════════════════════════════════════════════════════════
@router.get("/subscriptions")
async def list_subscriptions(
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(require_super_admin),
):
    """List all subscriptions."""
    db = SessionLocal()
    try:
        q = """
            SELECT s.id::text, s.pharmacy_id, p.name_ar AS pharmacy_name,
                   s.plan, s.status, s.price_monthly, s.currency,
                   s.started_at, s.expires_at, s.auto_renew
            FROM subscriptions s
            LEFT JOIN pharmacies p ON p.id = s.pharmacy_id
            WHERE 1=1
        """
        params = {}
        if status:
            q += " AND s.status = :status"
            params["status"] = status
        q += " ORDER BY s.created_at DESC LIMIT :limit"
        params["limit"] = limit

        result = db.execute(text(q), params)
        subs = [dict(r._mapping) for r in result]
        return {"subscriptions": subs, "count": len(subs)}
    finally:
        db.close()
