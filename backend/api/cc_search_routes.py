"""Control Center — Search + Export."""
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from auth.dependencies import require_admin
from auth.models import User
from db import SessionLocal
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/cc", tags=["cc-search"])


@router.get("/search")
async def global_search(q: str = Query(..., min_length=2), user: User = Depends(require_admin)):
    if len(q) < 2:
        return {"results": [], "count": 0}
    db = SessionLocal()
    results = []
    try:
        from sqlalchemy import text
        s = f"%{q.lower()}%"
        try:
            rows = db.execute(text("""
                SELECT 'product' AS type, "ItemCode" AS id, "ItemName" AS title
                FROM products WHERE LOWER("ItemName") LIKE :s OR LOWER("ItemCode") LIKE :s LIMIT 5
            """), {"s": s}).fetchall()
            results += [dict(r._mapping) for r in rows]
        except Exception: pass
        try:
            rows = db.execute(text("""
                SELECT 'drug' AS type, id::text, name AS title
                FROM drugs WHERE LOWER(name) LIKE :s LIMIT 5
            """), {"s": s}).fetchall()
            results += [dict(r._mapping) for r in rows]
        except Exception: pass
        try:
            rows = db.execute(text("""
                SELECT 'user' AS type, id, username AS title
                FROM users WHERE LOWER(username) LIKE :s OR LOWER(COALESCE(email,'')) LIKE :s LIMIT 5
            """), {"s": s}).fetchall()
            results += [dict(r._mapping) for r in rows]
        except Exception: pass
        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"results": [], "error": str(e)}
    finally:
        db.close()


@router.get("/export/metrics")
async def export_metrics(user: User = Depends(require_admin)):
    from api.monitoring_routes import _metrics, _start_time
    import time
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "server_uptime_seconds": int(time.time() - _start_time),
        "requests": list(_metrics["requests"]),
        "tool_calls": list(_metrics["tool_calls"]),
        "llm_calls": list(_metrics["llm_calls"]),
        "errors": list(_metrics["errors"]),
        "chat_activity": list(_metrics["chat_activity"]),
    }
