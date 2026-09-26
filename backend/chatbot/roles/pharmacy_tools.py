"""Pharmacy Tools — أدوات الصيدلي."""
from __future__ import annotations
from typing import Optional
import structlog

logger = structlog.get_logger()


def detect_tool(msg: str) -> Optional[str]:
    tool_keywords = {
        "my_stats": ["إحصائياتي", "إحصائيات صيدليتي", "my stats"],
        "my_orders": ["أوردراتي", "طلباتي", "my orders"],
        "my_customers": ["عملائي", "customers"],
        "drug_info": ["معلومات دواء", "معلومات عن", "drug info"],
        "drug_price": ["سعر", "بكام", "price"],
        "drug_alternatives": ["بديل", "بدائل", "alternatives"],
        "drug_interactions": ["تداخل", "interactions", "مع بعض"],
        "suggest_reply": ["اقترح رد", "رد على العميل", "ساعدني أرد", "suggest reply"],
        "my_whatsapp": ["حالة واتساب", "رقمي", "whatsapp status"],
    }
    scores = {}
    for tool, kws in tool_keywords.items():
        score = sum(1 for kw in kws if kw in msg)
        if score > 0:
            scores[tool] = score
    return max(scores, key=scores.get) if scores else None


async def execute(tool: str, context: dict) -> dict:
    handlers = {
        "my_stats": _my_stats,
        "my_orders": _my_orders,
        "my_customers": _my_customers,
        "drug_info": _drug_info,
        "drug_price": _drug_price,
        "drug_alternatives": _drug_alternatives,
        "drug_interactions": _drug_interactions,
        "suggest_reply": _suggest_reply,
        "my_whatsapp": _my_whatsapp,
    }
    handler = handlers.get(tool)
    if not handler:
        return {"reply": f"⚠️ أداة {tool} غير متاحة", "tools_used": [tool]}
    try:
        result = await handler(context)
        return {**result, "tools_used": [tool]}
    except Exception as e:
        logger.error("pharmacy.tool_failed", tool=tool, error=str(e))
        return {"reply": f"❌ فشل: {str(e)[:150]}", "tools_used": [tool]}


# ═══════════════ الأدوات ═══════════════

async def _my_stats(context: dict):
    pharmacy_id = context.get("pharmacy_id")
    if not pharmacy_id:
        return {"reply": "⚠️ مفيش صيدلية محددة"}
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        stats = {}
        for t in ["users", "products", "drugs"]:
            try:
                stats[t] = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() or 0
            except Exception:
                stats[t] = 0
        return {"reply": (
            f"📊 **إحصائيات صيدليتك**\n\n"
            f"👥 العملاء: {stats['users']}\n"
            f"📦 المنتجات: {stats['products']}\n"
            f"💊 الأدوية: {stats['drugs']}"
        ), "data": stats}
    finally:
        db.close()


async def _my_orders(context: dict):
    return {"reply": "📦 **آخر الأوردرات**\n\nجاري التطوير..."}


async def _my_customers(context: dict):
    return {"reply": "👥 **عملاؤك**\n\nجاري التطوير..."}


async def _drug_info(context: dict):
    return {"reply": "💊 اكتب اسم الدواء عشان أديك معلوماته"}


async def _drug_price(context: dict):
    return {"reply": "💰 اكتب اسم الدواء عشان أديك سعره"}


async def _drug_alternatives(context: dict):
    return {"reply": "🔄 اكتب اسم الدواء عشان أقترح بدائل"}


async def _drug_interactions(context: dict):
    return {"reply": "⚠️ اكتب أسماء الأدوية عشان أفحص التداخل"}


async def _suggest_reply(context: dict):
    """⭐ الميزة المهمة: اقتراح ردود على العملاء."""
    customer_question = context.get("customer_question", "")
    if not customer_question:
        return {"reply": (
            "💬 **اقتراح ردود على عميل**\n\n"
            "اكتب سؤال العميل، مثلاً:\n"
            "«العميل بيسأل عن دواء للصداع»\n"
            "«عميل عايز يعرف سعر البنادول»\n"
            "«عميل بيسأل عن بديل المضاد الحيوي»"
        )}

    # استخدام LLM لاقتراح ردود
    try:
        from chatbot.core import get_core
        core = get_core()
        prompt = f"""أنت مساعد صيدلي خبير. العميل سأل السؤال ده:
"{customer_question}"

اقترح 3 ردود احترافية مختلفة:
1. **مختصر** (1-2 سطر)
2. **مفصل** (معلومات + سعر + بدائل)
3. **ودود** (بأسلوب ودود مع إيموجي)

اكتب بالشكل ده:
🎯 **الرد 1 (مختصر):**
[الرد]

🎯 **الرد 2 (مفصل):**
[الرد]

🎯 **الرد 3 (ودود):**
[الرد]
"""
        response = await core.chat(
            message=prompt,
            channel="admin_assist",
            channel_user_id=context.get("user_id", "unknown"),
            pharmacy_id=context.get("pharmacy_id"),
        )
        return {"reply": response.text, "data": {"customer_question": customer_question}}
    except Exception as e:
        return {"reply": f"⚠️ فشل الاقتراح: {str(e)[:150]}"}


async def _my_whatsapp(context: dict):
    import httpx
    phone = context.get("phone")
    if not phone:
        return {"reply": "⚠️ مفيش رقم مسجل"}
    try:
        encoded = phone.replace("+", "%2B")
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"http://localhost:3001/sessions/{encoded}/status")
            data = r.json()
        status = data.get("status", "unknown")
        icon = "✅" if status == "connected" else "⏳"
        return {"reply": f"{icon} **حالة رقمك**\n\nالرقم: {phone}\nالحالة: {status}", "data": data}
    except Exception as e:
        return {"reply": f"❌ {e}"}
