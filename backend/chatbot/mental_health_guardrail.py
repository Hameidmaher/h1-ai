"""Mental Health Guardrail — منع وصف أدوية نفسية."""

EMOTIONAL_KEYWORDS = [
    "زهقان", "مبضون", "مخنوق", "زعلان", "حزين",
    "متضايق", "مش طايق", "مليت", "مكتئب شويه",
]

CLINICAL_KEYWORDS = [
    "اكتئاب", "قلق", "وسواس", "هلع", "suicide",
    "مش عايز أعيش", "أفكر في الانتحار",
]

PSYCH_MEDICATIONS = [
    "sertraline", "fluoxetine", "citalopram", "escitalopram",
    "paroxetine", "venlafaxine", "bupropion", "mirtazapine",
    "alprazolam", "diazepam", "lorazepam", "clonazepam",
    "زولفت", "بروزاك", "سيبرالكس", "زيروكسات",
]

RESPONSE_EMOTIONAL = (
    "💚 فاهم إنك ممكن تكون مش في أحسن حال.\n\n"
    "أنا مساعد صيدلية — مش مؤهل أقدم دعم نفسي متخصص.\n\n"
    "📞 خط نجدة الصحة النفسية: 08008880700\n\n"
    "لو عايز تفضفض، أنا هنا ✋"
)

RESPONSE_CLINICAL = (
    "🚨 *مهم*\n\n"
    "الأمر دا محتاج مختص.\n\n"
    "📞 خط نجدة الصحة النفسية: 08008880700\n"
    "🏥 توجه لأقرب مستشفى أو عيادة نفسية"
)

RESPONSE_CRISIS = (
    "💚 أنت لست وحدك.\n\n"
    "اتصل بـ:\n"
    "🚑 الطوارئ: 123\n"
    "📞 خط نجدة: 08008880700"
)


def check_mental_health(message: str):
    msg_lower = message.lower()

    crisis = ["انتحار", "أنتحر", "مش عايز أعيش", "أقتل نفسي", "suicide"]
    if any(k in msg_lower for k in crisis):
        return RESPONSE_CRISIS

    if any(k in msg_lower for k in CLINICAL_KEYWORDS):
        return RESPONSE_CLINICAL

    if any(k in msg_lower for k in EMOTIONAL_KEYWORDS):
        return RESPONSE_EMOTIONAL

    return None


def filter_psych_medications(response: str) -> str:
    for med in PSYCH_MEDICATIONS:
        if med.lower() in response.lower():
            return RESPONSE_CLINICAL
    return response
