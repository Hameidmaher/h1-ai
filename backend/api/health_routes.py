"""Health endpoints — optimized for speed."""
import time
from fastapi import APIRouter, Depends
from auth.dependencies import require_admin
from auth.models import User
from services.metrics import metrics

router = APIRouter(tags=["monitoring"])
START_TIME = time.time()

# ─── Health cache (5 seconds) ───
_health_cache = {"data": None, "time": 0}
_HEALTH_TTL = 5


@router.get("/health")
async def health():
    """Fast health check — cached for 5 seconds."""
    global _health_cache
    
    now = time.time()
    if _health_cache["data"] and (now - _health_cache["time"]) < _HEALTH_TTL:
        return _health_cache["data"]
    
    # Quick check only
    result = {
        "status": "healthy",
        "version": "5.0.0",
        "uptime_seconds": round(now - START_TIME, 1),
    }
    
    _health_cache["data"] = result
    _health_cache["time"] = now
    
    return result


@router.get("/health/deep")
async def health_deep():
    """Deep health check — slower, includes all checks."""
    checks = {}
    try:
        from knowledge.loader import knowledge_loader
        checks["knowledge_loaded"] = len(knowledge_loader.products) > 0
        checks["products_count"] = len(knowledge_loader.products)
    except Exception as e:
        checks["knowledge_loaded"] = False
        checks["knowledge_error"] = str(e)[:100]

    try:
        from knowledge.index.bm25_index import bm25_index
        checks["bm25_ready"] = bm25_index._built
    except Exception as e:
        checks["bm25_ready"] = False
        checks["bm25_error"] = str(e)[:100]

    try:
        from config_loader import prod_config
        checks["llm_provider"] = prod_config.llm_provider
    except Exception:
        checks["llm_provider"] = "unknown"

    all_ok = all(v for v in checks.values() if isinstance(v, bool))
    status = "healthy" if all_ok else "degraded"

    return {
        "status": status,
        "version": "5.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "checks": checks,
    }


@router.get("/ready")
async def ready():
    """Quick ready check — cached."""
    return {"ready": True}


@router.get("/live")
async def live():
    """Liveness probe."""
    return {"alive": True}


@router.get("/metrics")
async def get_metrics(user: User = Depends(require_admin)):
    """Get metrics (admin)."""
    return metrics.snapshot()


@router.post("/metrics/reset")
async def reset_metrics(user: User = Depends(require_admin)):
    """Reset metrics (admin)."""
    metrics.reset()
    return {"success": True}
