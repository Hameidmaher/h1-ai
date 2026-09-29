"""Chat Analytics — تتبع جودة المحادثات."""
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.dependencies import require_super_admin
from auth.models import User
from chatbot.roles.memory import get_stats as memory_stats

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/chat/analytics", tags=["chat-analytics"])


# In-memory analytics
_ANALYTICS = {
    "total_messages": 0,
    "by_role": {"admin": 0, "pharmacy": 0, "customer": 0},
    "by_hour": {},
    "ratings": {"up": 0, "down": 0},
    "avg_response_time_ms": 0,
    "response_times": [],
}


def record_message(role: str, response_time_ms: int = 0):
    """تسجيل رسالة."""
    _ANALYTICS["total_messages"] += 1
    _ANALYTICS["by_role"][role] = _ANALYTICS["by_role"].get(role, 0) + 1

    hour = datetime.now().strftime("%H:00")
    _ANALYTICS["by_hour"][hour] = _ANALYTICS["by_hour"].get(hour, 0) + 1

    if response_time_ms > 0:
        _ANALYTICS["response_times"].append(response_time_ms)
        if len(_ANALYTICS["response_times"]) > 100:
            _ANALYTICS["response_times"] = _ANALYTICS["response_times"][-100:]
        _ANALYTICS["avg_response_time_ms"] = sum(_ANALYTICS["response_times"]) / len(_ANALYTICS["response_times"])


class RatingRequest(BaseModel):
    message_id: str
    rating: str  # "up" or "down"


@router.get("/dashboard")
async def dashboard(user: User = Depends(require_super_admin)):
    """لوحة تحليلات الشات."""
    return {
        "total_messages": _ANALYTICS["total_messages"],
        "by_role": _ANALYTICS["by_role"],
        "by_hour": dict(sorted(_ANALYTICS["by_hour"].items())[-24:]),
        "ratings": _ANALYTICS["ratings"],
        "avg_response_time_ms": round(_ANALYTICS["avg_response_time_ms"], 2),
        "memory": memory_stats(),
    }


@router.post("/rate")
async def rate_message(req: RatingRequest, user: User = Depends(require_super_admin)):
    """تقييم رد."""
    if req.rating in ("up", "down"):
        _ANALYTICS["ratings"][req.rating] += 1
        return {"success": True, "ratings": _ANALYTICS["ratings"]}
    return {"success": False, "error": "invalid rating"}


@router.get("/roles")
async def roles_analytics(user: User = Depends(require_super_admin)):
    """تحليلات حسب الدور."""
    total = _ANALYTICS["total_messages"] or 1
    return {
        "total": _ANALYTICS["total_messages"],
        "admin": {
            "count": _ANALYTICS["by_role"].get("admin", 0),
            "percentage": round(_ANALYTICS["by_role"].get("admin", 0) / total * 100, 1),
        },
        "pharmacy": {
            "count": _ANALYTICS["by_role"].get("pharmacy", 0),
            "percentage": round(_ANALYTICS["by_role"].get("pharmacy", 0) / total * 100, 1),
        },
        "customer": {
            "count": _ANALYTICS["by_role"].get("customer", 0),
            "percentage": round(_ANALYTICS["by_role"].get("customer", 0) / total * 100, 1),
        },
    }
