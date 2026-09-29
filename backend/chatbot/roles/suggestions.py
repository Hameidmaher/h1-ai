"""اقتراحات ذكية بعد كل رد."""
from __future__ import annotations
from typing import List
import structlog

logger = structlog.get_logger()


# اقتراحات حسب الدور
ADMIN_SUGGESTIONS = [
    "📊 اعرض الإحصائيات",
    "🏪 قائمة الصيدليات",
    "👥 آخر 10 مستخدمين",
    "🛠️ حالة الخدمات",
    "📱 جلسات WhatsApp",
    "🕐 آخر 10 طلبات",
    "📜 آخر 20 سطر من اللوجات",
    "❤️ صحة النظام",
]

PHARMACY_SUGGESTIONS = [
    "📊 إحصائياتي",
    "📦 أوردراتي",
    "👥 عملائي",
    "💊 سعر البنادول",
    "🔄 بديل الفولتارين",
    "⭐ اقترح رد على عميل",
    "📱 حالة WhatsApp",
    "⚠️ افحص تداخلات",
]

CUSTOMER_SUGGESTIONS = [
    "💊 عايز بنادول",
    "💰 سعر الأموكسيسيلين",
    "🔄 بديل الفولتارين",
    "🩺 عندي صداع",
    "📦 عايز أطلب دواء",
    "🚚 تتبع الأوردر",
    "📍 عنوان الصيدلية",
    "📞 أكلم صيدلي",
]


def get_suggestions(role: str, last_message: str = "", limit: int = 4) -> List[str]:
    """يرجّع اقتراحات مناسبة."""
    base_suggestions = {
        "admin": ADMIN_SUGGESTIONS,
        "pharmacy": PHARMACY_SUGGESTIONS,
        "customer": CUSTOMER_SUGGESTIONS,
    }.get(role, CUSTOMER_SUGGESTIONS)

    # فلترة حسب السياق
    last_msg = last_message.lower() if last_message else ""

    # لو الرد فيه دواء، اقترح بدائل وسعر
    if any(w in last_msg for w in ["بنادول", "فولتارين", "باراسيتامول", "دواء", "سعر"]):
        contextual = ["💰 سعر الدواء", "🔄 بديل الدواء", "📦 اطلب الدواء", "⚠️ فحص التداخلات"]
        return contextual[:limit]

    # لو الرد عن أوردر
    if any(w in last_msg for w in ["أوردر", "طلب"]):
        contextual = ["🚚 تتبع الأوردر", "📦 أوردر تاني", "💰 الإجمالي", "❌ إلغاء"]
        return contextual[:limit]

    # اقتراحات عامة
    return base_suggestions[:limit]


def get_quick_actions(role: str) -> List[dict]:
    """أزرار سريعة حسب الدور."""
    actions = {
        "admin": [
            {"icon": "📊", "label": "إحصائيات", "action": "stats"},
            {"icon": "🏪", "label": "صيدليات", "action": "pharmacies"},
            {"icon": "🛠️", "label": "خدمات", "action": "services"},
            {"icon": "📱", "label": "واتساب", "action": "whatsapp"},
        ],
        "pharmacy": [
            {"icon": "📊", "label": "إحصائياتي", "action": "my_stats"},
            {"icon": "⭐", "label": "اقترح رد", "action": "suggest_reply"},
            {"icon": "💊", "label": "بحث دواء", "action": "drug_info"},
            {"icon": "📱", "label": "واتساب", "action": "my_whatsapp"},
        ],
        "customer": [
            {"icon": "💊", "label": "ابحث", "action": "find_drug"},
            {"icon": "💰", "label": "سعر", "action": "drug_price"},
            {"icon": "🔄", "label": "بدائل", "action": "drug_alternative"},
            {"icon": "📦", "label": "أوردر", "action": "place_order"},
        ],
    }
    return actions.get(role, actions["customer"])
