"""Endpoints صحة النظام والإحصائيات."""
import time
from fastapi import APIRouter, Depends
from auth.dependencies import require_admin
from auth.models import User
from services.metrics import metrics

router = APIRouter(tags=["monitoring"])
START_TIME = time.time()


@router.get("/health")
async def health():
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
    from knowledge.loader import knowledge_loader
    from knowledge.index.bm25_index import bm25_index
    if not knowledge_loader.products:
        return {"ready": False, "reason": "knowledge not loaded"}
    if not bm25_index._built:
        return {"ready": False, "reason": "bm25 not built"}
    return {"ready": True}


@router.get("/live")
async def live():
    return {"alive": True}


@router.get("/metrics")
async def get_metrics(user: User = Depends(require_admin)):
    return metrics.snapshot()


@router.post("/metrics/reset")
async def reset_metrics(user: User = Depends(require_admin)):
    metrics.reset()
    return {"success": True}
