"""H1-AI Guardrails - Input & Output validation for medical safety."""
import re
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class GuardResult:
    is_safe: bool
    reason: str = ""
    action: str = "allow"
    suggested_response: str = ""


class InputGuardrails:
    EMERGENCY_PATTERNS = [
        r"ألم\s*(في\s*)?(الصدر|القلب)",
        r"صعوبة\s*في\s*التنفس",
        r"ضيق\s*(في\s*)?(التنفس|النفس)",
        r"نزيف\s*(حاد|شديد|مستمر)",
        r"فقدان\s*الوعي",
        r"تشنجات",
        r"(جلطة|سكتة)\s*(قلبية|دماغية)",
        r"تسمم",
        r"جرعة\s*زائدة",
        r"chest\s+pain",
        r"difficulty\s+breathing",
        r"severe\s+bleeding",
        r"overdose",
        r"unconscious",
    ]
    SELF_HARM_PATTERNS = [
        r"(انتحار|أنتحر)",
        r"أذي\s*نفسي",
        r"أنهي\s*حياتي",
        r"suicide",
        r"kill\s+myself",
    ]
    FORBIDDEN_PATTERNS = [
        r"مخدرات", r"كوكايين", r"هيروين", r"حبوب\s*هلوسة",
        r"cocaine|heroin|meth",
    ]

    def check(self, message: str) -> GuardResult:
        if not message or not message.strip():
            return GuardResult(is_safe=False, reason="empty", action="block")
        m = message.lower()
        for p in self.EMERGENCY_PATTERNS:
            if re.search(p, m):
                return GuardResult(
                    is_safe=False, reason="emergency", action="escalate",
                    suggested_response=(
                        "🚨 حالة طارئة - اتصل بالإسعاف فورًا على 123\n\n"
                        "لو الأعراض دي عندك:\n"
                        "• ألم شديد في الصدر\n"
                        "• صعوبة في التنفس\n"
                        "• فقدان وعي\n\n"
                        "اتصل بالطوارئ الآن."
                    ),
                )
        for p in self.SELF_HARM_PATTERNS:
            if re.search(p, m):
                return GuardResult(
                    is_safe=False, reason="self_harm", action="escalate",
                    suggested_response=(
                        "أنا هنا لمساعدتك، لكن دي حالة محتاجة دعم متخصص.\n\n"
                        "📞 الخط الساخن للدعم النفسي: 08008880700"
                    ),
                )
        for p in self.FORBIDDEN_PATTERNS:
            if re.search(p, m):
                return GuardResult(
                    is_safe=False, reason="forbidden", action="block",
                    suggested_response="آسف، مش قادر أساعد في الموضوع ده.",
                )
        return GuardResult(is_safe=True)


class OutputGuardrails:
    DISCLAIMER = (
        "\n\n---\n"
        "⚠️ تنبيه: المعلومات دي للإرشاد فقط، ومش بديل عن استشارة الطبيب أو الصيدلي. "
        "لو الأعراض مستمرة، راجع طبيبك فورًا."
    )
    RX_ONLY_DRUGS = [
        "amoxicillin", "augmentin", "ciprofloxacin",
        "morphine", "tramadol", "diazepam",
        "warfarin", "insulin", "metformin",
    ]

    def check(self, response: str) -> GuardResult:
        if not response or not response.strip():
            return GuardResult(is_safe=False, reason="empty", action="block")
        r = response.lower()
        mentions_rx = any(d in r for d in self.RX_ONLY_DRUGS)
        medical_kw = ["دواء", "علاج", "جرعة", "medicine", "treatment", "dose"]
        has_medical = any(k in r for k in medical_kw)

        if mentions_rx and "طبيب" not in response:
            return GuardResult(is_safe=True, action="warn",
                reason="rx_warning",
                suggested_response=response + self.DISCLAIMER)
        if has_medical and self.DISCLAIMER.strip() not in response:
            return GuardResult(is_safe=True, action="warn",
                reason="medical_advice",
                suggested_response=response + self.DISCLAIMER)
        return GuardResult(is_safe=True, action="allow",
            suggested_response=response)


input_guard = InputGuardrails()
output_guard = OutputGuardrails()
