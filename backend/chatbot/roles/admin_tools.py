"""Admin Tools — أدوات Super Admin."""
from __future__ import annotations
import subprocess
from typing import Optional
import structlog

logger = structlog.get_logger()


def detect_tool(msg: str) -> Optional[str]:
    """كشف الأداة المطلوبة."""
    tool_keywords = {
        "stats": ["إحصائيات", "stats", "كم عدد", "الأرقام"],
        "pharmacies": ["صيدليات", "صيدلية", "pharmacies", "المشتركين"],
        "users": ["مستخدمين", "users", "العملاء"],
        "services": ["خدمات", "services", "حالة النظام", "السيرفرات"],
        "whatsapp": ["واتساب", "whatsapp", "جلسات"],
        "activity": ["نشاط", "activity", "طلبات", "requests", "آخر"],
        "logs": ["لوجات", "logs", "سجلات", "errors"],
        "restart_wa": ["إعادة تشغيل واتساب", "restart whatsapp", "شغل واتساب"],
        "restart_api": ["إعادة تشغيل api", "restart api", "شغل السيرفر"],
        "clear_logs": ["امسح اللوجات", "clear logs", "نظف"],
        "revenue": ["إيرادات", "revenue", "الفلوس", "الأرباح"],
        "health": ["صحة النظام", "health check", "فحص"],
    }
    scores = {}
    for tool, keywords in tool_keywords.items():
        score = sum(1 for kw in keywords if kw in msg)
        if score > 0:
            scores[tool] = score
    return max(scores, key=scores.get) if scores else None


async def execute(tool: str, context: dict) -> dict:
    """تنفيذ الأداة."""
    handlers = {
        "stats": _stats,
        "pharmacies": _pharmacies,
        "users": _users,
        "services": _services,
        "whatsapp": _whatsapp,
        "activity": _activity,
        "logs": _logs,
        "restart_wa": _restart_wa,
        "restart_api": _restart_api,
        "clear_logs": _clear_logs,
        "revenue": _revenue,
        "health": _health,
    }
    handler = handlers.get(tool)
    if not handler:
        return {"reply": f"⚠️ أداة {tool} غير متاحة", "tools_used": [tool]}
    try:
        result = await handler()
        return {**result, "tools_used": [tool]}
    except Exception as e:
        logger.error("admin.tool_failed", tool=tool, error=str(e))
        return {"reply": f"❌ فشل: {str(e)[:150]}", "tools_used": [tool]}


# ═══════════════ الأدوات ═══════════════

async def _stats():
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        s = {}
        for t in ["users", "pharmacies", "products", "drugs"]:
            try:
                s[t] = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() or 0
            except Exception:
                s[t] = 0
        return {"reply": (
            f"📊 **إحصائيات المنصة**\n\n"
            f"👥 المستخدمون: **{s['users']}**\n"
            f"🏪 الصيدليات: **{s['pharmacies']}**\n"
            f"📦 المنتجات: **{s['products']}**\n"
            f"💊 الأدوية: **{s['drugs']}**"
        ), "data": s}
    finally:
        db.close()


async def _pharmacies():
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        try:
            rows = db.execute(text("""
                SELECT id, name, phone, is_active FROM pharmacies
                ORDER BY created_at DESC LIMIT 20
            """)).fetchall()
            items = [dict(r._mapping) for r in rows]
        except Exception:
            items = []
        if not items:
            return {"reply": "🏪 مفيش صيدليات مسجلة", "data": []}
        lines = [f"🏪 **الصيدليات** ({len(items)})", ""]
        for p in items:
            icon = "✅" if p.get("is_active") else "❌"
            lines.append(f"{icon} {p.get('name', '—')} — {p.get('phone', '—')}")
        return {"reply": "\n".join(lines), "data": items}
    finally:
        db.close()


async def _users():
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT username, role, is_active, created_at FROM users
            ORDER BY created_at DESC LIMIT 10
        """)).fetchall()
        lines = ["👥 **آخر 10 مستخدمين**\n"]
        for u in rows:
            icon = "✅" if u.is_active else "❌"
            lines.append(f"{icon} {u.username} ({u.role})")
        return {"reply": "\n".join(lines), "data": [dict(r._mapping) for r in rows]}
    except Exception as e:
        return {"reply": f"⚠️ {e}"}
    finally:
        db.close()


async def _services():
    services = ["h1ai", "h1ai-whatsapp", "postgresql", "redis-server", "nginx", "tailscaled"]
    status = {}
    for svc in services:
        try:
            r = subprocess.run(["systemctl", "is-active", svc],
                             capture_output=True, text=True, timeout=2)
            status[svc] = r.stdout.strip() or "unknown"
        except Exception:
            status[svc] = "error"
    lines = ["🛠️ **حالة الخدمات**\n"]
    for svc, st in status.items():
        icon = "✅" if st == "active" else "❌"
        lines.append(f"{icon} {svc}: {st}")
    return {"reply": "\n".join(lines), "data": status}


async def _whatsapp():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://localhost:3001/sessions")
            data = r.json()
        sessions = data.get("sessions", [])
        if not sessions:
            return {"reply": "📱 مفيش جلسات WhatsApp نشطة", "data": []}
        lines = [f"📱 **جلسات WhatsApp** ({len(sessions)})", ""]
        for s in sessions:
            icon = "✅" if s.get("status") == "connected" else "⏳"
            lines.append(f"{icon} {s.get('phone_number')} — {s.get('status')}")
        return {"reply": "\n".join(lines), "data": sessions}
    except Exception as e:
        return {"reply": f"❌ {e}"}


async def _activity():
    from api.monitoring_routes import _metrics
    reqs = list(_metrics["requests"])[-10:]
    if not reqs:
        return {"reply": "🕐 مفيش نشاط حديث", "data": []}
    lines = ["🕐 **آخر 10 طلبات**\n"]
    for r in reversed(reqs):
        lines.append(f"  {r['method']} {r['path']} → {r['status']}")
    return {"reply": "\n".join(lines), "data": reqs}


async def _logs():
    try:
        r = subprocess.run(["sudo", "tail", "-20", "/var/log/h1ai.log"],
                          capture_output=True, text=True, timeout=5)
        return {"reply": f"📜 **آخر 20 سطر**\n```\n{r.stdout[-1500:]}\n```"}
    except Exception as e:
        return {"reply": f"❌ {e}"}


async def _restart_wa():
    try:
        r = subprocess.run(["sudo", "systemctl", "restart", "h1ai-whatsapp.service"],
                          capture_output=True, text=True, timeout=15)
        return {"reply": "✅ تم إعادة تشغيل WhatsApp" if r.returncode == 0 else f"❌ {r.stderr[:150]}"}
    except Exception as e:
        return {"reply": f"❌ {e}"}


async def _restart_api():
    try:
        r = subprocess.run(["sudo", "systemctl", "restart", "h1ai.service"],
                          capture_output=True, text=True, timeout=15)
        return {"reply": "✅ تم إعادة تشغيل API" if r.returncode == 0 else f"❌ {r.stderr[:150]}"}
    except Exception as e:
        return {"reply": f"❌ {e}"}


async def _clear_logs():
    paths = ["/var/log/h1ai.log", "/home/h/h1-ai/whatsapp-service/service.log"]
    cleared = []
    for p in paths:
        try:
            subprocess.run(["sudo", "truncate", "-s", "0", p], check=True, timeout=5)
            cleared.append(p)
        except Exception:
            pass
    return {"reply": f"✅ تم تصفير {len(cleared)} log"}


async def _revenue():
    return {"reply": "💰 تقرير الإيرادات قيد التطوير"}


async def _health():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://localhost:8000/health")
            return {"reply": f"✅ **حالة النظام**\n\n{r.json()}"}
    except Exception as e:
        return {"reply": f"❌ {e}"}
