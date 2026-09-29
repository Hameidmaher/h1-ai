"""Memory System — تذكر السياق لكل مستخدم."""
from __future__ import annotations
import time
from collections import defaultdict, deque
from typing import Optional
import structlog

logger = structlog.get_logger()

# In-memory store (يمكن استبداله بـ Redis لاحقاً)
_MEMORY = {
    "sessions": defaultdict(lambda: deque(maxlen=20)),  # آخر 20 رسالة
    "prefs": defaultdict(dict),                          # تفضيلات المستخدم
    "context": defaultdict(dict),                        # سياق المحادثة
}


def get_session_key(user_id: str, role: str) -> str:
    return f"{role}:{user_id}"


def add_message(user_id: str, role: str, message: str, sender: str = "user"):
    """يضيف رسالة للسياق."""
    key = get_session_key(user_id, role)
    _MEMORY["sessions"][key].append({
        "sender": sender,
        "message": message,
        "ts": time.time(),
    })


def get_context(user_id: str, role: str, limit: int = 10) -> str:
    """يرجّع السياق كـ string."""
    key = get_session_key(user_id, role)
    history = list(_MEMORY["sessions"][key])[-limit:]
    if not history:
        return ""
    lines = []
    for h in history:
        sender = "المستخدم" if h["sender"] == "user" else "أنت"
        lines.append(f"{sender}: {h['message']}")
    return "\n".join(lines)


def set_pref(user_id: str, key: str, value):
    """حفظ تفضيل."""
    _MEMORY["prefs"][user_id][key] = value


def get_pref(user_id: str, key: str, default=None):
    """قراءة تفضيل."""
    return _MEMORY["prefs"][user_id].get(key, default)


def set_context(user_id: str, key: str, value):
    """حفظ في السياق."""
    _MEMORY["context"][user_id][key] = value


def get_context_data(user_id: str, key: str, default=None):
    """قراءة من السياق."""
    return _MEMORY["context"][user_id].get(key, default)


def clear_session(user_id: str, role: str):
    """مسح محادثة."""
    key = get_session_key(user_id, role)
    _MEMORY["sessions"][key].clear()
    logger.info("memory.cleared", user=user_id, role=role)


def get_stats():
    """إحصائيات الذاكرة."""
    return {
        "active_sessions": len(_MEMORY["sessions"]),
        "total_users": len(_MEMORY["prefs"]),
        "total_contexts": len(_MEMORY["context"]),
    }
