"""Admin pharmacies routes — /v1/admin/pharmacies/*."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_admin
from services.pharmacy_service import pharmacy_service
from services.whatsapp_bridge import whatsapp_bridge
from db import SessionLocal
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin/pharmacies", tags=["admin-pharmacies"])


# ═══════════════════════════════════════════════════════════
#  BASIC CRUD (5)
# ═══════════════════════════════════════════════════════════
@router.get("")
async def list_pharmacies(user: User = Depends(require_admin)):
    """List all pharmacies."""
    return {"pharmacies": pharmacy_service.list_pharmacies()}


@router.get("/{pharmacy_id}")
async def get_pharmacy(pharmacy_id: str, user: User = Depends(require_admin)):
    """Get one pharmacy."""
    p = pharmacy_service.get_pharmacy(pharmacy_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    return p


@router.post("")
async def create_pharmacy(request: Request, user: User = Depends(require_admin)):
    """Create new pharmacy."""
    data = await request.json()
    if not data.get("name"):
        raise HTTPException(status_code=400, detail="Name required")
    return pharmacy_service.create_pharmacy(data)


@router.put("/{pharmacy_id}")
async def update_pharmacy(pharmacy_id: str, request: Request, user: User = Depends(require_admin)):
    """Update pharmacy."""
    data = await request.json()
    result = pharmacy_service.update_pharmacy(pharmacy_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    return result


@router.delete("/{pharmacy_id}")
async def delete_pharmacy(pharmacy_id: str, user: User = Depends(require_admin)):
    """Soft delete pharmacy."""
    pharmacy_service.delete_pharmacy(pharmacy_id)
    return {"success": True}


# ═══════════════════════════════════════════════════════════
#  HARD DELETE (2)
# ═══════════════════════════════════════════════════════════
@router.delete("/{pharmacy_id}/hard")
async def hard_delete_pharmacy(pharmacy_id: str, user: User = Depends(require_admin)):
    """Hard delete pharmacy + all related data."""
    db = SessionLocal()
    try:
        numbers = db.execute(text("""
            SELECT phone_number FROM whatsapp_numbers WHERE pharmacy_id = :pid
        """), {"pid": pharmacy_id}).fetchall()

        for row in numbers:
            try:
                await whatsapp_bridge.delete_session(row[0])
            except Exception:
                pass

        result = db.execute(text("DELETE FROM pharmacies WHERE id = :pid"), {"pid": pharmacy_id})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pharmacy not found")

        logger.info("pharmacy.hard_deleted", pharmacy_id=pharmacy_id)
        return {"success": True, "deleted": True, "pharmacy_id": pharmacy_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:100])
    finally:
        db.close()


@router.delete("/{pharmacy_id}/hard-delete")
async def pharmacy_hard_delete(pharmacy_id: str, user: User = Depends(require_admin)):
    """Hard delete with WhatsApp session cleanup."""
    db = SessionLocal()
    try:
        numbers = db.execute(text("""
            SELECT phone_number FROM whatsapp_numbers WHERE pharmacy_id = :pid
        """), {"pid": pharmacy_id}).fetchall()
    finally:
        db.close()

    disconnected = 0
    for row in numbers:
        try:
            r = await whatsapp_bridge.delete_session(row[0])
            if r.get("success"):
                disconnected += 1
        except Exception:
            pass

    db = SessionLocal()
    try:
        result = db.execute(text("DELETE FROM pharmacies WHERE id = :pid"), {"pid": pharmacy_id})
        db.commit()
        return {
            "success": True,
            "pharmacy_id": pharmacy_id,
            "deleted": result.rowcount > 0,
            "sessions_disconnected": disconnected,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  SUSPEND / ACTIVATE (2)
# ═══════════════════════════════════════════════════════════
@router.post("/{pharmacy_id}/suspend")
async def pharmacy_suspend(pharmacy_id: str, user: User = Depends(require_admin)):
    """Suspend pharmacy — disable but keep data."""
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE pharmacies SET is_active = FALSE, updated_at = NOW()
            WHERE id = :pid
        """), {"pid": pharmacy_id})
        db.commit()
        return {"success": True, "action": "suspended", "pharmacy_id": pharmacy_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()


@router.post("/{pharmacy_id}/activate")
async def pharmacy_activate(pharmacy_id: str, user: User = Depends(require_admin)):
    """Reactivate suspended pharmacy."""
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE pharmacies SET is_active = TRUE, updated_at = NOW()
            WHERE id = :pid
        """), {"pid": pharmacy_id})
        db.commit()
        return {"success": True, "action": "activated", "pharmacy_id": pharmacy_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
#  FULL UPDATE (1)
# ═══════════════════════════════════════════════════════════
@router.put("/{pharmacy_id}/full-update")
async def pharmacy_full_update(pharmacy_id: str, request: Request, user: User = Depends(require_admin)):
    """Full update of pharmacy data (whitelist columns)."""
    data = await request.json()

    ALLOWED_COLS = {
        "name", "name_ar", "phone", "email", "address",
        "city", "governorate", "latitude", "longitude",
        "is_active", "subscription_status", "notes",
    }
    updates = {k: v for k, v in data.items() if k in ALLOWED_COLS}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields")

    set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
    updates["pid"] = pharmacy_id

    db = SessionLocal()
    try:
        result = db.execute(text(f"""
            UPDATE pharmacies
            SET {set_clause}, updated_at = NOW()
            WHERE id = :pid
        """), updates)
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pharmacy not found")

        ph = db.execute(text("""
            SELECT id::text, name, name_ar, phone, email, address, city,
                   subscription_plan, is_active, created_at, updated_at
            FROM pharmacies WHERE id = :pid
        """), {"pid": pharmacy_id}).first()

        return {"success": True, "pharmacy": dict(ph._mapping) if ph else None}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)[:200])
    finally:
        db.close()
