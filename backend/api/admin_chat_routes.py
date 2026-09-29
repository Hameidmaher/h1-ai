"""Admin Chat — شات بوت للمدير العام (Super Admin)."""
from __future__ import annotations
import os
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import require_super_admin
from auth.models import User
from db import SessionLocal

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin/chat", tags=["admin-chat"])


class AdminChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class AdminChatResponse(BaseModel):
    reply: str
    data: Optional[dict] = None
    tools_used: list = []


# ═══════════════════════════════════════════════════════════════════
# الأدوات الإدارية
# ═══════════════════════════════════════════════════════════════════

async def tool_get_stats():
    """إحصائيات عامة للمنصة."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        stats = {}
        for table in ["users", "pharmacies", "products", "drugs"]:
            try:
                stats[table] = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
            except Exception:
                stats[table] = 0
        return {
            "type": "stats",
            "data": stats,
            "reply": f"📊 **إحصائيات المنصة**\n\n"
                     f"👥 المستخدمون: {stats.get('users', 0)}\n"
                     f"🏪 الصيدليات: {stats.get('pharmacies', 0)}\n"
                     f"📦 المنتجات: {stats.get('products', 0)}\n"
                     f"💊 الأدوية: {stats.get('drugs', 0)}"
        }
    finally:
        db.close()


async def tool_list_pharmacies():
    """قائمة الصيدليات."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        try:
            rows = db.execute(text("""
                SELECT id, name, phone, is_active, created_at
                FROM pharmacies ORDER BY created_at DESC LIMIT 20
            """)).fetchall()
            items = [dict(r._mapping) for r in rows]
        except Exception:
            items = []
        if not items:
            return {"reply": "🏪 مفيش صيدليات مسجلة حتى الآن", "data": []}
        text_out = "🏪 **آخر 20 صيدلية**\n\n"
        for p in items:
            status = "✅" if p.get("is_active") else "❌"
            text_out += f"{status} {p.get('name', '—')} — {p.get('phone', '—')}\n"
        return {"reply": text_out, "data": items}
    finally:
        db.close()


async def tool_service_status():
    """حالة الخدمات."""
    import subprocess
    services = ["h1ai", "h1ai-whatsapp", "postgresql", "redis-server", "nginx", "tailscaled"]
    status = {}
    for svc in services:
        try:
            r = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=2
            )
            status[svc] = r.stdout.strip() or "unknown"
        except Exception:
            status[svc] = "error"
    lines = ["🛠️ **حالة الخدمات**\n"]
    for svc, st in status.items():
        icon = "✅" if st == "active" else "❌"
        lines.append(f"{icon} {svc}: {st}")
    return {"reply": "\n".join(lines), "data": status}


async def tool_whatsapp_sessions():
    """جلسات WhatsApp."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:3001/sessions")
            data = r.json()
        sessions = data.get("sessions", [])
        if not sessions:
            return {"reply": "📱 مفيش جلسات WhatsApp نشطة", "data": sessions}
        lines = [f"📱 **جلسات WhatsApp** ({len(sessions)})", ""]
        for s in sessions:
            icon = "✅" if s.get("status") == "connected" else "⏳"
            lines.append(f"{icon} {s.get('phone_number')} — {s.get('status')}")
        return {"reply": "\n".join(lines), "data": sessions}
    except Exception as e:
        return {"reply": f"❌ فشل الاتصال بـ WhatsApp service: {e}", "data": None}


async def tool_recent_activity():
    """آخر النشاطات."""
    from api.monitoring_routes import _metrics
    reqs = list(_metrics["requests"])[-10:]
    if not reqs:
        return {"reply": "🕐 مفيش نشاط حديث", "data": []}
    lines = ["🕐 **آخر 10 طلبات**\n"]
    for r in reversed(reqs):
        lines.append(f"  {r['method']} {r['path']} → {r['status']} ({r['duration_ms']}ms)")
    return {"reply": "\n".join(lines), "data": reqs}


async def tool_restart_whatsapp():
    """إعادة تشغيل WhatsApp service."""
    import subprocess
    try:
        r = subprocess.run(
            ["sudo", "systemctl", "restart", "h1ai-whatsapp.service"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            return {"reply": "✅ تم إعادة تشغيل WhatsApp service", "data": {"success": True}}
        return {"reply": f"❌ فشل: {r.stderr[:200]}", "data": {"success": False}}
    except Exception as e:
        return {"reply": f"❌ {e}", "data": None}


async def tool_clear_logs():
    """تصفير الـ logs."""
    import subprocess
    paths = ["/var/log/h1ai.log", "/home/h/h1-ai/whatsapp-service/service.log"]
    cleared = []
    for p in paths:
        try:
            subprocess.run(["sudo", "truncate", "-s", "0", p], check=True, timeout=5)
            cleared.append(p)
        except Exception:
            pass
    return {"reply": f"✅ تم تصفير {len(cleared)} log", "data": {"cleared": cleared}}


# ═══════════════════════════════════════════════════════════════════
# الأدوات المتاحة
# ═══════════════════════════════════════════════════════════════════
ADMIN_TOOLS = {
    "stats": (tool_get_stats, ["إحصائيات", "stats", "كم", "عدد"]),
    "pharmacies": (tool_list_pharmacies, ["صيدليات", "صيدلية", "pharmacies"]),
    "services": (tool_service_status, ["خدمات", "services", "حالة", "systemctl"]),
    "whatsapp": (tool_whatsapp_sessions, ["واتساب", "whatsapp", "جلسات", "sessions"]),
    "activity": (tool_recent_activity, ["نشاط", "activity", "طلبات", "requests", "آخر"]),
    "restart_wa": (tool_restart_whatsapp, ["إعادة تشغيل", "restart", "whatsapp"]),
    "clear_logs": (tool_clear_logs, ["امسح", "clear", "log", "لوج"]),
}


def _detect_tool(message: str) -> Optional[str]:
    """يكتشف الأداة المطلوبة من الرسالة."""
    msg = message.lower()
    scores = {}
    for tool_name, (_, keywords) in ADMIN_TOOLS.items():
        score = sum(1 for kw in keywords if kw in msg)
        if score > 0:
            scores[tool_name] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


# ═══════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.post("/send", response_model=AdminChatResponse)
async def admin_chat_send(
    req: AdminChatRequest,
    user: User = Depends(require_super_admin),
):
    """الشات الإداري للمدير العام."""
    logger.info("admin.chat", user=user.username, message=req.message[:100])

    message = req.message.strip()
    if not message:
        raise HTTPException(400, "الرسالة فاضية")

    # كشف الأداة
    tool_name = _detect_tool(message)

    if tool_name:
        tool_func, _ = ADMIN_TOOLS[tool_name]
        try:
            result = await tool_func()
            return AdminChatResponse(
                reply=result.get("reply", "—"),
                data=result.get("data"),
                tools_used=[tool_name],
            )
        except Exception as e:
            logger.error("admin.chat.tool_failed", tool=tool_name, error=str(e))
            return AdminChatResponse(
                reply=f"❌ فشل تنفيذ {tool_name}: {str(e)[:150]}",
                tools_used=[tool_name],
            )

    # لو مفيش أداة، نرد بقائمة المساعدة
    help_text = """🤖 **مرحباً بك في مساعد الإدارة**

أنا بوت بيساعدك في إدارة المنصة. جرب:

📊 **إحصائيات** — "اعرض الإحصائيات"
🏪 **صيدليات** — "قائمة الصيدليات"
🛠️ **خدمات** — "حالة الخدمات"
📱 **واتساب** — "جلسات واتساب"
🕐 **نشاط** — "آخر الطلبات"
🔄 **إعادة تشغيل** — "restart whatsapp"
🧹 **تنظيف** — "امسح اللوجات"

أو اكتب "مساعدة" لعرض القائمة دي تاني."""
    return AdminChatResponse(reply=help_text, tools_used=[])


@router.get("/help")
async def admin_chat_help(user: User = Depends(require_super_admin)):
    """قائمة الأدوات المتاحة."""
    return {
        "tools": list(ADMIN_TOOLS.keys()),
        "examples": [
            "اعرض الإحصائيات",
            "قائمة الصيدليات",
            "حالة الخدمات",
            "جلسات واتساب",
            "آخر الطلبات",
            "restart whatsapp",
            "امسح اللوجات",
        ]
    }
