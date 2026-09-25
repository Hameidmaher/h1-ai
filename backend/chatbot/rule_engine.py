"""Rule Engine — with priorities and confidence scoring.

Each rule has:
- pattern: regex to match
- response: text to return
- rule_id: unique identifier
- priority: higher = checked first (default 50)
- confidence: how sure we are (default 0.99)
"""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class RuleMatch:
    response: str
    rule_id: str
    confidence: float = 0.99


class RuleEngine:
    # Format: (pattern, response, rule_id, priority, confidence)
    # Priority: 100 = exact match, 50 = normal, 10 = loose
    RULES: list[tuple[str, str, str, int, float]] = [
        # ─── Greetings (high priority, exact) ───
        (r"^(ال)?سلام\s*عليكم[.!؟\s]*$",
         "وعليكم السلام ورحمة الله وبركاته 🌟", "greeting_salam", 100, 0.99),
        (r"^(أهلا|أهلاً|هاي|hi|hello|مرحبا|مرحباً)[.!؟\s]*$",
         "أهلاً وسهلاً! إزاي أقدر أساعدك؟", "greeting_hello", 100, 0.99),
        (r"^(صباح الخير|صباح النور)[.!؟\s]*$",
         "صباح النور والسرور! ☀️", "greeting_morning", 100, 0.99),
        (r"^(مساء الخير|مساء النور)[.!؟\s]*$",
         "مساء النور! 🌙", "greeting_evening", 100, 0.99),
        # ═══ جديد ═══
        (r"^(إزيك|إزيك|ازيك|إزاي حالك|إيه أخبارك|أخبارك إيه|عامل إيه|عاملة إيه|إيه الأخبار|كيف حالك|كيفك)[.!؟\s]*$",
         "الحمد لله، بخير! إزاي أقدر أساعدك؟ 😊", "greeting_howareyou", 100, 0.99),

        # ─── Thanks ───
        (r"^(شكرا|شكراً|تسلم|تسلمي|مشكور|مشكورة)[.!؟\s]*$",
         "العفو، في خدمتك دائماً 😊", "thanks", 100, 0.99),

        # ─── Farewell ───
        (r"^(مع السلامة|باي|bye|إلى اللقاء|الى اللقاء)[.!؟\s]*$",
         "في رعاية الله، نورتنا!", "farewell", 100, 0.99),

        # ─── FAQ ───
        (r"(ساعات العمل|امتى تفتحوا|امتى تقفلوا|مواعيد العمل)",
         "من 9 صباحاً حتى 11 مساءً، طوال الأسبوع ⏰", "hours", 80, 0.95),
        (r"(هل )?عندكم توصيل|بتوصلوا|فيه توصيل",
         "نعم، التوصيل متوفر داخل المدينة 🚚", "delivery", 80, 0.95),
        (r"(العنوان|فين المحل|مكانكم|موقعكم)",
         "📍 العنوان: شارع رئيسي، وسط المدينة", "location", 80, 0.95),
        (r"(رقم التليفون|رقم الهاتف|كيف أتواصل)",
         "📞 للتواصل: 0123 456 7890", "phone", 80, 0.95),
    ]

    def match(self, message: str) -> RuleMatch | None:
        """Find best matching rule by priority."""
        if not message or not message.strip():
            return None

        msg = message.strip()
        matches: list[tuple[int, RuleMatch]] = []

        for pattern, response, rule_id, priority, confidence in self.RULES:
            try:
                if re.search(pattern, msg, re.IGNORECASE):
                    matches.append((
                        priority,
                        RuleMatch(
                            response=response,
                            rule_id=rule_id,
                            confidence=confidence,
                        )
                    ))
            except re.error:
                continue

        if not matches:
            return None

        # Return highest priority match
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]


rule_engine = RuleEngine()
