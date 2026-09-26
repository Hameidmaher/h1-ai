"""Customer Tools — أدوات عميل الصيدلية."""
from __future__ import annotations
from typing import Optional
import structlog

logger = structlog.get_logger()


def detect_tool(msg: str) -> Optional[str]:
    tool_keywords = {
        "find_drug": ["عايز", "عندكم", "دوء", "علاج", "دوا"],
        "drug_price": ["سعر", "بكام", "كم"],
        "drug_alternative": ["بديل", "بدائل"],
        "check_symptoms": ["أعراض", "عندي", "حاسس", "وجع", "ألم"],
        "place_order": ["أوردر", "اطلب", "عايز أطلب"],
        "track_order": ["طلبي", "فين أوردر", "تتبع"],
        "store_info": ["الصيدلية", "العنوان", "مواعيد", "تليفون"],
        "human_handoff": ["صيدلي", "أكلم حد", "بشري"],
    }
    scores = {}
    for tool, kws in tool_keywords.items():
        score = sum(1 for kw in kws if kw in msg)
        if score > 0:
            scores[tool] = score
    return max(scores, key=scores.get) if scores else None


async def execute(tool: str, context: dict) -> dict:
    handlers = {
        "find_drug": _find_drug,
        "drug_price": _drug_price,
        "drug_alternative": _drug_alternative,
        "check_symptoms": _check_symptoms,
        "place_order": _place_order,
        "track_order": _track_order,
        "store_info": _store_info,
        "human_handoff": _human_handoff,
    }
    handler = handlers.get(tool)
    if not handler:
        return {"reply": "أنا هنا أساعدك 🩺", "tools_used": [tool]}
    try:
        result = await handler(context)
        return {**result, "tools_used": [tool]}
    except Exception as e:
        logger.error("customer.tool_failed", tool=tool, error=str(e))
        return {"reply": "⚠️ معلش حصلت مشكلة، حاول تاني 🙏", "tools_used": [tool]}


async def _find_drug(context: dict):
    return {"reply": "💊 اكتب اسم الدواء اللي بتدور عليه، وأنا هقولك متوفر ولا لأ"}


async def _drug_price(context: dict):
    return {"reply": "💰 اكتب اسم الدواء، وأنا هقولك سعره"}


async def _drug_alternative(context: dict):
    return {"reply": "🔄 اكتب اسم الدواء، وأنا هقولك بدائله"}


async def _check_symptoms(context: dict):
    return {"reply": (
        "🩺 **قولي إيه اللي حاسس بيه**\n\n"
        "مثلاً: «عندي صداع»، «حاسس بحرقان في المعدة»\n\n"
        "⚠️ ملاحظة: أنا مش بديل عن الطبيب. للحالات الخطيرة اتصل بالطوارئ."
    )}


async def _place_order(context: dict):
    return {"reply": "📦 اكتب اسم الدواء والكمية، وأنا هجهزلك الأوردر"}


async def _track_order(context: dict):
    return {"reply": "🚚 اكتب رقم الأوردر، وأنا هقولك حالته"}


async def _store_info(context: dict):
    return {"reply": "📍 **معلومات الصيدلية**\n\nجاري التطوير..."}


async def _human_handoff(context: dict):
    return {"reply": "👨‍⚕️ **جاري تحويلك لصيدلي بشري**\n\nاستنى لحظات..."}
