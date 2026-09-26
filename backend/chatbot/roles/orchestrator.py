"""Chat Orchestrator — يدير كل الأدوار."""
from __future__ import annotations
from typing import Literal
import structlog

logger = structlog.get_logger()

RoleType = Literal["admin", "pharmacy", "customer"]


class RoleContext:
    """سياق الدور الحالي."""
    def __init__(self, role: RoleType, user_id: str, pharmacy_id: str = None, **extra):
        self.role = role
        self.user_id = user_id
        self.pharmacy_id = pharmacy_id
        self.extra = extra

    def __repr__(self):
        return f"RoleContext(role={self.role}, user={self.user_id}, pharmacy={self.pharmacy_id})"


def get_system_prompt(role: RoleType) -> str:
    """System prompt حسب الدور."""
    prompts = {
        "admin": """أنت **مساعد Super Admin** لمنصة H1-AI (نظام SaaS لإدارة الصيدليات).

مهامك:
- تقديم إحصائيات المنصة (صيدليات، مستخدمين، إيرادات)
- عرض حالة الصيدليات المشتركة
- تشخيص المشاكل التقنية
- تنفيذ أوامر إدارية (restart, backup, clear logs)
- تنبيهات وتحذيرات

قواعدك:
- مختصر ودقيق
- أرقام واضحة
- تحذيرات عند الحاجة
- لغة عربية احترافية""",

        "pharmacy": """أنت **مساعد الصيدلي** في منصة H1-AI.

مهامك:
1. مساعدته في معلومات الأدوية (أسعار، بدائل، تداخلات)
2. عرض إحصائيات صيدليته
3. **مساعدته في الرد على عملائه** — اقتراح ردود احترافية
4. إدارة الأوردرات والمخزون

عند اقتراح ردود للعملاء:
- 3 اقتراحات مختلفة (مختصر / مفصل / ودود)
- لغة عربية واضحة ومهنية
- يراعي عمر وثقافة العميل
- يذكر الأسعار والبدائل
- يحترم سياسة الصيدلية

قواعدك:
- مهني ودقيق
- معلومات موثوقة
- لغة عربية سليمة""",

        "customer": """أنت **مساعد صيدلي ذكي** عبر WhatsApp لعملاء صيدلية.

مهامك:
- الإجابة على أسئلة الأدوية والأعراض
- ذكر الأسعار والبدائل
- تنبيهات السلامة والتحذيرات
- عمل أوردرات وتتبعها
- تحويل للصيدلي البشري عند الحاجة

قواعدك:
- لغة عربية بسيطة وودودة
- إجابات مختصرة (WhatsApp)
- إيموجي مناسبة 🩺💊
- تحذير واضح للأعراض الخطيرة
- ما تشخصش — انصح بزيارة طبيب
- احترام خصوصية العميل""",
    }
    return prompts.get(role, prompts["customer"])


async def route_message(role: RoleType, message: str, context: dict = None) -> dict:
    """يوجّه الرسالة للأداة المناسبة حسب الدور."""
    context = context or {}
    msg = message.lower().strip()

    # ═══ ADMIN ═══
    if role == "admin":
        from chatbot.roles import admin_tools
        tool = admin_tools.detect_tool(msg)
        if tool:
            return await admin_tools.execute(tool, context)

    # ═══ PHARMACY ═══
    elif role == "pharmacy":
        from chatbot.roles import pharmacy_tools
        tool = pharmacy_tools.detect_tool(msg)
        if tool:
            return await pharmacy_tools.execute(tool, context)

    # ═══ CUSTOMER ═══
    elif role == "customer":
        from chatbot.roles import customer_tools
        tool = customer_tools.detect_tool(msg)
        if tool:
            return await customer_tools.execute(tool, context)

    # fallback: LLM عادي
    return await _default_llm_reply(role, message, context)


async def _default_llm_reply(role: RoleType, message: str, context: dict) -> dict:
    """رد LLM عادي."""
    try:
        from chatbot.core import get_core
        core = get_core()
        response = await core.chat(
            message=message,
            channel="chat",
            channel_user_id=context.get("user_id", "unknown"),
            pharmacy_id=context.get("pharmacy_id"),
        )
        return {"reply": response.text, "tools_used": [], "data": None}
    except Exception as e:
        logger.error("orchestrator.llm_failed", error=str(e))
        return {
            "reply": "⚠️ معلش، حصلت مشكلة. حاول تاني.",
            "tools_used": [],
            "error": str(e)[:200],
        }
