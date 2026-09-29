"""Pharmacist Agent — نسخة مبسّطة بدون LangGraph."""
from __future__ import annotations

import threading
import time
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import AgentResponse
from llm.factory import create_llm
from agents.safety_guardrails import check_safety
from core.text_utils import normalize_message, should_use_normalized
import structlog

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════════
#  Simple Cache
# ═══════════════════════════════════════════════════════════
class SimpleCache:
    """TTL cache بسيط للردود."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self._cache: dict = {}
        self._ttl = ttl_seconds
        self._max = max_size
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value):
        with self._lock:
            if len(self._cache) >= self._max:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[key] = (value, time.time() + self._ttl)


_simple_cache = SimpleCache()


# ═══════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════
def should_need_human(text: str, original_message: str = "") -> bool:
    """تحديد إذا كان الرد يحتاج تدخل بشري."""
    if not text:
        return False

    # 1. ردود أسعار/منتجات → مش محتاج
    price_indicators = ["السعر", "الكود", "ج.م", "جنيه", "الكمية المتوفرة", "كود الصنف"]
    if any(k in text for k in price_indicators):
        if "|" in text and ("السعر" in text or "الكود" in text):
            return False

    # 2. ردود غير طبية → مش محتاج
    non_medical = [
        "كيف يمكنني مساعدتك", "كيف حالك", "أنا بخير", "مرحباً بك",
        "وعليكم السلام", "العفو", "أهلاً وسهلاً", "شكراً جزيلاً",
    ]
    if any(phrase in text for phrase in non_medical):
        if len(text) < 200:
            return False

    # 3. تحذيرات طبية → محتاج
    medical_alerts = [
        "حساسية", "تداخل دوائي", "تحذير", "استشر طبيب", "استشارة",
        "الحمل", "الأطفال", "جرعة زائدة", "أعراض جانبية",
        "تفاعل دوائي", "منعت", "ممنوع",
    ]
    if any(k in text for k in medical_alerts):
        return True

    # 4. Emergency → محتاج
    emergency = ["اتصل", "الطوارئ", "الإسعاف", "123", "فوراً"]
    if any(k in text for k in emergency):
        return True

    # 5. توصيات دوائية → محتاج
    medical_recs = ["يُنصح", "ينصح", "استخدم", "البديل", "تناول"]
    if any(k in text for k in medical_recs):
        if len(text) > 300 and "السعر" not in text:
            return True

    return False


def detect_out_of_scope(message: str) -> str | None:
    """كشف الأسئلة خارج النطاق الطبي."""
    out_of_scope_kw = [
        "السياسة", "الرياضة", "الأخبار", "الطقس", "البرمجة",
        "الأفلام", "الأغاني", "المسلسلات", "الطبخ",
    ]
    msg = message.lower()
    for kw in out_of_scope_kw:
        if kw in msg:
            return kw
    return None


def make_scope_response(scope: str) -> str:
    return (
        f"أنا مساعد صيدلي — مش متخصص في {scope}.\n"
        "لكن لو عندك أي سؤال عن الأدوية أو الصحة، أنا هنا! 💊"
    )


def check_emotional(message: str) -> str | None:
    """كشف الحالة النفسية."""
    emotional_kw = [
        "زهقان", "مبضون", "مخنوق", "حزين", "متضايق",
        "مش طايق", "مليت", "مكتئب",
    ]
    msg = message.lower()
    for kw in emotional_kw:
        if kw in msg:
            return (
                "💚 فاهم إنك ممكن تكون مش في أحسن حال.\n\n"
                "أنا مساعد صيدلية — مش مؤهل أقدم دعم نفسي متخصص.\n"
                "📞 خط نجدة الصحة النفسية: 08008880700"
            )
    return None


# ═══════════════════════════════════════════════════════════
#  Pharmacist Agent
# ═══════════════════════════════════════════════════════════
SYSTEM_PROMPT = (
    "أنت مساعد صيدلي محترف في H1-AI.\n\n"
    "مهامك:\n"
    "1. ساعد الصيدلي في إدارة المخزون.\n"
    "2. حلل الطلبات والتقارير.\n"
    "3. اقترح تحسينات.\n\n"
    "أسلوبك: عربي مهني، موجز، دقيق."
)


class PharmacistAgent:
    MAX_ITERATIONS = 5

    def __init__(self):
        self.llm = create_llm(temperature=0.2)

    def process(self, message: str) -> AgentResponse:
        logger.info("pharmacist_agent.process", message=message[:80])

        # 1. Cache
        cached = _simple_cache.get(message)
        if cached is not None:
            return cached

        # 2. ضمان string
        safe_message = str(message) if message else ""
        if not safe_message.strip():
            safe_message = "مرحبا"

        # 3. Safety
        is_safe, safety_response = check_safety(safe_message)
        if not is_safe and safety_response:
            result = AgentResponse(
                text=safety_response,
                action="answer",
                confidence=1.0,
                needs_human=False,
            )
            _simple_cache.set(message, result)
            return result

        # 4. Emotional
        emotional = check_emotional(safe_message)
        if emotional:
            result = AgentResponse(
                text=emotional,
                action="answer",
                confidence=0.9,
                needs_human=False,
            )
            _simple_cache.set(message, result)
            return result

        # 5. Fuzzy
        normalized = normalize_message(safe_message)
        if should_use_normalized(safe_message, normalized):
            safe_message = normalized

        # 6. Out of scope
        scope = detect_out_of_scope(safe_message)
        if scope:
            result = AgentResponse(
                text=make_scope_response(scope),
                action="answer",
                confidence=0.95,
                needs_human=False,
            )
            _simple_cache.set(message, result)
            return result

        # 7. LLM call (بدون tools!)
        try:
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=safe_message),
            ]
            response = self.llm.invoke(messages)
            text = response.content if isinstance(response.content, str) else str(response.content)

            needs_human = should_need_human(text, safe_message)

            result = AgentResponse(
                text=text,
                action="answer",
                confidence=0.85,
                needs_human=needs_human,
            )
            _simple_cache.set(message, result)
            return result

        except Exception as e:
            logger.error("pharmacist_agent.error", error=str(e)[:200])
            return AgentResponse(
                text=(
                    "عذراً، حصل خطأ مؤقت. ممكن تحاول تاني؟\n\n"
                    "لو المشكلة استمرت، اتصل بالدعم الفني."
                ),
                action="answer",
                confidence=0.0,
                needs_human=True,
            )
