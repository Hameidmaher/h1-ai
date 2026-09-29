"""
Safety Guardrails — حماية متقدمة
"""
import re


# ═══════════════════════════════════════════════════════════
# Safety Rules — قواعد الأمان
# ═══════════════════════════════════════════════════════════

SAFETY_RULES = {
    "abortion": {
        "keywords": [
            "إجهاض", "اجهاض", "أجهض", "اجهض", "إسقاط الحمل",
            "abortion", "abort", "mifepristone", "misoprostol",
            "حبوب الإجهاض", "سايتوتيك", "ميفيبريستون",
        ],
        "response": (
            "أنا مساعد صيدلي، ومش من صلاحياتي المساعدة في موضوع الإجهاض. "
            "الموضوع ده يحتاج **إشراف طبي كامل** في مستشفى أو عيادة متخصصة. "
            "لو أنت في موقف صعب، أنصحك تتواصل مع **طبيب نساء وتوليد** "
            "أو **جهة صحية موثوقة** في بلدك. "
            "أنا هنا لو احتجت أي مساعدة طبية تانية."
        ),
    },
    "drug_abuse": {
        "keywords": [
            "أشرب وأسوق", "أشرب وأسوق", "أسوق وأنا سكران",
            "دوا يخليني أسكر", "دوا للسكر", "دوا مخدر",
            "drug abuse", "get high", "intoxicated driving",
        ],
        "response": (
            "لا يمكنني المساعدة في أي شيء يتعلق بالقيادة تحت تأثير "
            "المخدرات أو الكحول — ده **خطر على حياتك وحياة الآخرين**، "
            "و**مخالف للقانون** في كل الدول. "
            "لو بتعاني من مشكلة إدمان، فيه جهات متخصصة تقدر تساعدك. "
            "أنا هنا لأي استفسار طبي آمن."
        ),
    },
    "prompt_injection": {
        "patterns": [
            r"system\s*:\s*",
            r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts)",
            r"reveal\s+(all\s+)?(api\s*keys?|secrets?|passwords?)",
            r"show\s+me\s+(your\s+)?(system\s*prompt|instructions)",
            r"اطبع\s+(محتوى\s+)?\.env",
            r"اعرض\s+(كل\s+)?(الأسرار|المفاتيح|API)",
            r"تجاهل\s+(كل\s+)?(التعليمات|الأوامر)\s+السابقة",
        ],
        "response": (
            "أنا مساعد صيدلي مخصص للاستفسارات الطبية والصحية. "
            "مش هقدر أساعد في أي طلبات من النوع ده. "
            "لو عندك سؤال عن دواء أو عرض صحي، أنا في الخدمة."
        ),
    },
    "identity_change": {
        "patterns": [
            r"(انت|أنت)\s+(مش|لست)\s+(بوت|مساعد)\s+(طبي|صيدلي)",
            r"(you\s+are|you're)\s+not\s+a\s+(medical|pharmacy)\s+bot",
            r"(pretend|act)\s+(to\s+be|as)\s+",
            r"تصرف\s+كأنك\s+",
            r"انت\s+الآن\s+في\s+وضع\s+المطور",
            r"developer\s+mode",
        ],
        "response": (
            "أنا مساعد صيدلي من H1-AI، ومهمتي مساعدتك في الاستفسارات "
            "الطبية والدوائية. مش هقدر أتظاهر بدور تاني أو أتجاوز تخصصي. "
            "لو عندك سؤال طبي، أنا في الخدمة."
        ),
    },
    "self_harm": {
        "keywords": [
            "أموت", "انتحار", "أنتحر", "أقتل نفسي",
            "suicide", "kill myself", "end my life",
            "إيذاء نفسي", "أجرح نفسي",
        ],
        "response": (
            "أنا قلقان عليك جداً. لو بتمر بوقت صعب، إنت مش لوحدك. 💙\n\n"
            "**اتصل فوراً بـ:**\n"
            "- **الطوارئ:** 123 (مصر) / 911 (السعودية) / 999 (الإمارات)\n"
            "- **خط الدعم النفسي:** 08008880700 (مصر)\n\n"
            "ممكن كمان تتكلم مع حد تثق فيه من عيلتك أو أصحابك. "
            "حياتك مهمة، وفيه ناس كتير عاوزة تساعدك. 🙏"
        ),
    },
}


def check_safety(message: str) -> tuple[bool, str | None]:
    """
    يفحص الرسالة من ناحية الأمان.
    يرجّع (safe: bool, response: str | None)
    """
    if not message:
        return True, None
    
    msg_lower = message.lower()
    
    for rule_name, rule in SAFETY_RULES.items():
        # فحص keywords
        keywords = rule.get("keywords", [])
        for kw in keywords:
            if kw.lower() in msg_lower:
                return False, rule["response"]
        
        # فحص patterns
        patterns = rule.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return False, rule["response"]
    
    return True, None
