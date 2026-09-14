from langchain_core.messages import AIMessage
from typing import Sequence
import structlog

logger = structlog.get_logger()


def check_tool_calls_allowed(
    tool_calls: Sequence[dict],
    allowed: set[str],
) -> tuple[bool, str | None]:
    for tc in tool_calls:
        name = tc.get("name")
        if name not in allowed:
            logger.warning("guardrail.forbidden_tool", tool=name)
            return False, f"الأداة '{name}' غير مسموحة"
    return True, None


def make_refusal_message(reason: str) -> AIMessage:
    return AIMessage(content=(
        "عذراً، لا أستطيع تنفيذ هذا الطلب لأنه خارج نطاق صلاحياتي. "
        "لو محتاج مساعدة إضافية، ممكن تتواصل مع الصيدلي مباشرة."
    ))
