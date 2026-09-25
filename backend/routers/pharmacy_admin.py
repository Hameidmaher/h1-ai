"""Pharmacy Admin routes — /v1/pharmacy/* (per-tenant management)."""
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_pharmacy_access
from auth.jwt_handler import hash_password
from db import SessionLocal

router = APIRouter(prefix="/v1/pharmacy", tags=["pharmacy-admin"])


# ═══════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════
def _get_pharmacy_id(user: User) -> str:
    """Get pharmacy_id from user."""
    if not user.pharmacy_id:
        raise HTTPException(403, "المستخدم مش مربوط بصيدلية")
    return user.pharmacy_id


# ═══════════════════════════════════════════════════════════
#  PHARMACY INFO
# ═══════════════════════════════════════════════════════════
@router.get("/me")
async def get_my_pharmacy(user: User = Depends(require_pharmacy_access)):
    """Get current pharmacy info."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, name_ar, phone, email, address, city,
                   logo_url, subscription_plan, subscription_expires_at,
                   is_active, settings, created_at
            FROM pharmacies WHERE id = :pid
        """), {"pid": pid}).first()

        if not result:
            raise HTTPException(404, "الصيدلية غير موجودة")

        return dict(result._mapping)
    finally:
        db.close()


@router.get("/stats")
async def get_my_stats(user: User = Depends(require_pharmacy_access)):
    """Get pharmacy statistics."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM users WHERE pharmacy_id = :pid) AS users,
                (SELECT COUNT(*) FROM users WHERE pharmacy_id = :pid AND role = 'pharmacist') AS pharmacists,
                (SELECT COUNT(*) FROM messages WHERE pharmacy_id = :pid) AS total_messages,
                (SELECT COUNT(*) FROM messages WHERE pharmacy_id = :pid AND received_at >= CURRENT_DATE) AS messages_today,
                (SELECT COUNT(*) FROM conversations WHERE pharmacy_id = :pid) AS conversations,
                (SELECT COUNT(*) FROM conversations WHERE pharmacy_id = :pid AND unread_count > 0) AS unread_conversations,
                (SELECT COUNT(*) FROM products WHERE pharmacy_id = :pid) AS products,
                (SELECT COUNT(*) FROM inventory WHERE pharmacy_id = :pid) AS inventory_items
        """), {"pid": pid})
        return dict(result.first()._mapping)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  PRODUCTS
# ═══════════════════════════════════════════════════════════
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None
    price: float = 0
    stock_qty: int = 0
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock_qty: Optional[int] = None
    description: Optional[str] = None


@router.get("/products")
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_pharmacy_access),
):
    """List products for current pharmacy."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        q = """
            SELECT id::text, name, category, price, stock_qty, description,
                   barcode, created_at
            FROM products WHERE pharmacy_id = :pid
        """
        params = {"pid": pid}
        if category:
            q += " AND category = :category"
            params["category"] = category
        if search:
            q += " AND name ILIKE :search"
            params["search"] = f"%{search}%"
        q += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = db.execute(text(q), params)
        products = [dict(r._mapping) for r in result]
        return {"products": products, "count": len(products)}
    finally:
        db.close()


@router.post("/products")
async def create_product(
    data: ProductCreate,
    user: User = Depends(require_pharmacy_access),
):
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        item_code = str(uuid4())
        db.execute(text("""
            INSERT INTO products (id, item_code, name, category, price, stock_qty,
                                  description, pharmacy_id)
            VALUES (:id, :item_code, :name, :category, :price, :stock_qty,
                    :description, :pid)
        """), {
            "id": item_code,
            "item_code": item_code[:20],
            "name": data.name,
            "category": data.category,
            "price": data.price,
            "stock_qty": data.stock_qty,
            "description": data.description,
            "pid": pid,
        })
        db.commit()
        return {"success": True, "id": item_code}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e)[:200])
    finally:
        db.close()


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    data: ProductUpdate,
    user: User = Depends(require_pharmacy_access),
):
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return {"success": True}

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["pid"] = pid
        updates["id"] = product_id

        db.execute(text(f"""
            UPDATE products SET {set_clause}, updated_at = NOW()
            WHERE id = :id AND pharmacy_id = :pid
        """), updates)
        db.commit()
        return {"success": True}
    finally:
        db.close()


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    user: User = Depends(require_pharmacy_access),
):
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        db.execute(text("""
            DELETE FROM products WHERE id = :id AND pharmacy_id = :pid
        """), {"id": product_id, "pid": pid})
        db.commit()
        return {"success": True}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  DRUGS
# ═══════════════════════════════════════════════════════════
@router.get("/drugs")
async def list_drugs(
    search: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(require_pharmacy_access),
):
    """List drugs (shared or pharmacy-specific)."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        q = """
            SELECT id::text, trade_name, trade_name_en, scientific_name,
                   category, form, strength, price_egp, prescription_required
            FROM drugs WHERE pharmacy_id = :pid OR pharmacy_id IS NULL
        """
        params = {"pid": pid, "limit": limit}
        if search:
            q += " AND (trade_name ILIKE :search OR trade_name_en ILIKE :search OR scientific_name ILIKE :search)"
            params["search"] = f"%{search}%"
        if category:
            q += " AND category = :category"
            params["category"] = category
        q += " ORDER BY trade_name LIMIT :limit"

        result = db.execute(text(q), params)
        drugs = [dict(r._mapping) for r in result]
        return {"drugs": drugs, "count": len(drugs)}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  WHATSAPP
# ═══════════════════════════════════════════════════════════
@router.get("/whatsapp")
async def list_whatsapp_numbers(user: User = Depends(require_pharmacy_access)):
    """List WhatsApp numbers for current pharmacy."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id::text, phone_number, status, is_primary,
                   connected_at, created_at
            FROM whatsapp_numbers WHERE pharmacy_id = :pid
            ORDER BY is_primary DESC, created_at DESC
        """), {"pid": pid})
        numbers = [dict(r._mapping) for r in result]
        return {"numbers": numbers, "count": len(numbers)}
    finally:
        db.close()


@router.get("/whatsapp/health")
async def whatsapp_health(user: User = Depends(require_pharmacy_access)):
    """Check WhatsApp service health."""
    from services.whatsapp_bridge import whatsapp_bridge
    try:
        health = await whatsapp_bridge.health()
        return health
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════
#  ORDERS
# ═══════════════════════════════════════════════════════════
@router.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_pharmacy_access),
):
    """List orders for current pharmacy."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        q = """
            SELECT id::text, customer_phone, customer_name, status,
                   total_amount, items_count, created_at, updated_at
            FROM orders WHERE pharmacy_id = :pid
        """
        params = {"pid": pid, "limit": limit, "offset": offset}
        if status:
            q += " AND status = :status"
            params["status"] = status
        q += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

        result = db.execute(text(q), params)
        orders = [dict(r._mapping) for r in result]
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        # الجدول ممكن مش موجود
        return {"orders": [], "count": 0, "error": str(e)[:100]}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  TEAM
# ═══════════════════════════════════════════════════════════
@router.get("/team")
async def list_team(
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(require_pharmacy_access),
):
    """List team members for current pharmacy."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, username, email, phone, full_name, role,
                   is_active, created_at
            FROM users WHERE pharmacy_id = :pid
            ORDER BY role, username
            LIMIT :limit
        """), {"pid": pid, "limit": limit})
        members = [dict(r._mapping) for r in result]
        return {"members": members, "count": len(members)}
    finally:
        db.close()


class TeamMemberCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(pharmacist|customer)$")
    full_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None


@router.post("/team")
async def add_team_member(
    data: TeamMemberCreate,
    user: User = Depends(require_pharmacy_access),
):
    """Add a team member (pharmacist/customer only)."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
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
                    :email, :phone, :pid, TRUE)
        """), {
            "id": uid,
            "username": data.username,
            "hash": hash_password(data.password),
            "role": data.role,
            "full_name": data.full_name,
            "email": data.email,
            "phone": data.phone,
            "pid": pid,
        })
        db.commit()
        return {"success": True, "id": uid}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e)[:200])
    finally:
        db.close()


@router.delete("/team/{user_id}")
async def remove_team_member(
    user_id: str,
    user: User = Depends(require_pharmacy_access),
):
    """Remove a team member from pharmacy."""
    pid = _get_pharmacy_id(user)
    if user_id == user.id:
        raise HTTPException(400, "لا يمكن حذف نفسك")

    db = SessionLocal()
    try:
        # Soft: unassign from pharmacy
        db.execute(text("""
            UPDATE users SET pharmacy_id = NULL, is_active = FALSE, updated_at = NOW()
            WHERE id = :id AND pharmacy_id = :pid
        """), {"id": user_id, "pid": pid})
        db.commit()
        return {"success": True}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════
class PharmacySettings(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    logo_url: Optional[str] = None


@router.put("/settings")
async def update_settings(
    data: PharmacySettings,
    user: User = Depends(require_pharmacy_access),
):
    """Update pharmacy settings."""
    pid = _get_pharmacy_id(user)
    db = SessionLocal()
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return {"success": True}

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["pid"] = pid

        db.execute(text(f"""
            UPDATE pharmacies SET {set_clause}, updated_at = NOW()
            WHERE id = :pid
        """), updates)
        db.commit()
        return {"success": True}
    finally:
        db.close()
