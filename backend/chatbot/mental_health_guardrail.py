"""Mental Health Guardrail — منع وصف أدوية نفسية + كشف حالات الخطر."""

EMOTIONAL_KEYWORDS = [
    "زهقان", "مبضون", "مخنوق", "زعلان", "حزين",
    "متضايق", "مش طايق", "مليت", "مكتئب شويه",
]

CLINICAL_KEYWORDS = [
    "اكتئاب", "قلق", "وسواس", "هلع", "suicide",
    "مش عايز أعيش", "أفكر في الانتحار",
]

# ═══════════════════════════════════════════════════════════
#  CRISIS KEYWORDS (أولوية عالية)
# ═══════════════════════════════════════════════════════════
CRISIS_KEYWORDS = [
    # انتحار
    "انتحار", "أنتحر", "أفكر في الانتحار", "أفكر في انتحار",
    "عايز انتحر", "عاوز انتحر", "هنتحر",
    # الموت
    "عايز أموت", "عاوز أموت", "عايز اموت", "عاوز اموت",
    "نفسي أموت", "نفسي اموت", "أتمنى أموت", "اتمنى اموت",
    "أموت", "اموت", "أموت خلاص", "اموت خلاص",
    # مش عايز أعيش
    "مش عايز أعيش", "مش عاوز أعيش", "مش عايز اعيش", "مش عاوز اعيش",
    "مش عاوزة أعيش", "مش عاوزة اعيش",
    "مش عايز أكمل", "مش عاوز أكمل",
    "مش عايز أعيش تاني", "مش عاوز أعيش تاني",
    # إيذاء النفس
    "هأذي نفسي", "هاذي نفسي", "هأذى نفسي",
    "أأذي نفسي", "أأذى نفسي",
    "جرحت نفسي", "أجرح نفسي", "أقطع نفسي",
    "هقطع نفسي", "قطع نفسي",
    "بأذي نفسي", "باذي نفسي",
    # قتل النفس
    "أقتل نفسي", "اقتل نفسي", "هقتل نفسي", "هقتل نفسي",
    # يأس
    "عايز أموت خلاص", "عاوز اموت خلاص",
    "مفيش فايدة", "مفيش فايده", "مفيش أمل", "مفيش امل",
    "أنا تعبان", "أنا تعبانة",
    # English
    "suicide", "kill myself", "end my life", "want to die",
    "self harm", "hurt myself",
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
    "📞 خط نجدة الصحة النفسية: 08008880700\n\n"
    "لو في خطر مباشر، روح أقرب مستشفى أو اتصل بحد قريب منك."
)


def check_mental_health(message: str) -> str | None:
    """فحص الرسالة — يرجّع رد إذا كانت فيها مشكلة نفسية."""
    if not message:
        return None

    msg_lower = message.lower()

    # 1. 🚨 CRISIS (أولوية عالية)
    if any(k in msg_lower for k in CRISIS_KEYWORDS):
        return RESPONSE_CRISIS

    # 2. CLINICAL (اكتئاب، قلق، إلخ)
    if any(k in msg_lower for k in CLINICAL_KEYWORDS):
        return RESPONSE_CLINICAL

    # 3. EMOTIONAL (زهقان، حزين، إلخ)
    if any(k in msg_lower for k in EMOTIONAL_KEYWORDS):
        return RESPONSE_EMOTIONAL

    return None


def filter_psych_medications(response: str) -> str:
    """منع وصف أدوية نفسية."""
    for med in PSYCH_MEDICATIONS:
        if med.lower() in response.lower():
            return RESPONSE_CLINICAL
    return response
