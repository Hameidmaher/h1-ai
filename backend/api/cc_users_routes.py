"""Control Center — Users API."""
from fastapi import APIRouter, Depends, Query, HTTPException
from auth.dependencies import require_admin, require_super_admin
from auth.models import User
from db import SessionLocal
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/cc/users", tags=["cc-users"])


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    role: str = Query(""),
    active: str = Query(""),
    search: str = Query(""),
    user: User = Depends(require_admin),
):
    db = SessionLocal()
    try:
        from sqlalchemy import text
        where, params = [], {"l": size, "o": (page - 1) * size}
        if role:
            where.append("role = :role"); params["role"] = role
        if active in ("true", "false"):
            where.append("is_active = :active"); params["active"] = active == "true"
        if search:
            where.append("(LOWER(username) LIKE :s OR LOWER(COALESCE(email,'')) LIKE :s)")
            params["s"] = f"%{search.lower()}%"
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        q = f"""SELECT id, username, email, role, is_active, pharmacy_id, created_at
            FROM users {where_sql} ORDER BY created_at DESC NULLS LAST LIMIT :l OFFSET :o"""
        rows = db.execute(text(q), params).fetchall()
        cp = {k: v for k, v in params.items() if k not in ("l", "o")}
        total = db.execute(text(f"SELECT COUNT(*) FROM users {where_sql}"), cp).scalar() or 0
        return {"items": [dict(r._mapping) for r in rows], "total": total,
                "page": page, "size": size, "pages": max(1, (total + size - 1) // size)}
    except Exception as e:
        logger.error("cc.users.list.failed", error=str(e))
        return {"items": [], "total": 0, "error": str(e)}
    finally:
        db.close()


@router.get("/stats")
async def users_stats(user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        from sqlalchemy import text
        total = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        active = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar() or 0
        rows = db.execute(text("SELECT role, COUNT(*) as cnt FROM users GROUP BY role")).fetchall()
        return {"total": total, "active": active, "inactive": total - active,
                "by_role": {r.role: r.cnt for r in rows}}
    except Exception as e:
        return {"total": 0, "active": 0, "inactive": 0, "by_role": {}, "error": str(e)}
    finally:
        db.close()


@router.post("/{user_id}/toggle")
async def toggle_user(user_id: str, user: User = Depends(require_super_admin)):
    db = SessionLocal()
    try:
        from sqlalchemy import text
        row = db.execute(text("UPDATE users SET is_active = NOT is_active WHERE id = :id RETURNING is_active"),
                         {"id": user_id}).fetchone()
        db.commit()
        if not row:
            raise HTTPException(404, "المستخدم غير موجود")
        logger.warning("cc.users.toggle", by=user.username, target=user_id, new_state=row[0])
        return {"success": True, "is_active": row[0]}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
