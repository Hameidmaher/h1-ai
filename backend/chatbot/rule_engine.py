from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class RuleMatch:
    response: str
    rule_id: str


class RuleEngine:
    RULES = [
        (r"^(ال)?سلام.*عليكم", "وعليكم السلام ورحمة الله 🌟", "greeting"),
        (r"^(أهلا|هاي|hi|hello|مرحبا)", "أهلاً وسهلاً! إزاي أقدر أساعدك؟", "greeting"),
        (r"(شكرا|شكراً|تسلم|مشكور)", "العفو، في خدمتك دائماً 😊", "thanks"),
        (r"(مع السلامة|باي|bye)", "في رعاية الله، نورتنا!", "farewell"),
        (r"ساعات العمل", "من 9 صباحاً حتى 11 مساءً، طوال الأسبوع ⏰", "hours"),
        (r"(هل )?عندكم توصيل", "نعم، التوصيل متوفر داخل المدينة 🚚", "delivery"),
    ]

    def match(self, message: str) -> RuleMatch | None:
        msg = message.strip().lower()
        for pattern, response, rule_id in self.RULES:
            if re.search(pattern, msg):
                return RuleMatch(response=response, rule_id=rule_id)
        return None


rule_engine = RuleEngine()
