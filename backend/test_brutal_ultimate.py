#!/usr/bin/env python3
"""
💀💀💀 H1-AI Chatbot — ULTIMATE BRUTAL TEST
400+ سؤال × 50 فئة × تقييم متعدد المستويات + Concurrency
"""
import asyncio
import sys
sys.path.insert(0, '/home/h/h1-ai/backend')

import time
import json
import re
import random
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════════════════════════════════
# 400+ سؤال في 50 فئة
# ═══════════════════════════════════════════════════════════════════

CUSTOMER_TESTS = {
    # ─── البحث الأساسي ───
    "🔍 بحث بأسماء أدوية شائعة": [
        "بنادول", "باراسيتامول", "فولتارين", "بروفين", "أموكسيسيلين",
        "أسبرين", "كونجستال", "تلفاست", "زيرتك", "أوميبرازول",
        "نيكسيوم", "لوسك", "كريستاس", "بيتادين", "ريفو",
    ],
    "🔍 بحث بأسماء إنجليزية": [
        "Panadol", "Paracetamol", "Voltaren", "Brufen", "Amoxicillin",
        "Aspirin", "Congestal", "Telfast", "Zyrtec", "Omeprazole",
        "Ibuprofen", "Diclofenac", "Ciprofloxacin", "Metformin",
    ],
    "🔍 بحث بأسماء خاطئة": [
        "بنادل", "بانادول", "بنادو", "باراسيتامو", "بارستامول",
        "فولتارينن", "برفين", "اموكسسلين", "اموكس", "تلفست",
        "زيرتكك", "كونجستل", "نكسيوم", "اوميبرازل", "اسبرينة",
    ],
    # ─── صيغ الطلب ───
    "🛒 صيغ طلب مباشرة": [
        "عايز بنادول", "محتاج فولتارين", "عندكم أموكسيسيلين؟",
        "ممكن بروفين؟", "لو سمحت أسبرين", "عايز اشتري دواء",
        "محتاج حاجة للصداع", "بدور على مسكن", "عايز مسكن قوي",
    ],
    "🛒 صيغ طلب غير مباشرة": [
        "لو تكرمت أقدر ألاقي إيه؟", "محتاج مساعدة",
        "ممكن تدلني على حاجة؟", "عندك اقتراح؟",
        "إيه اللي تنصح بيه؟", "مش عارف أعمل إيه",
    ],
    # ─── الأسعار ───
    "💰 أسعار مباشرة": [
        "بكام البنادول؟", "سعر الفولتارين", "الباراسيتامول بكام؟",
        "إيه تكلفة الأموكسيسيلين؟", "البروفين بكام؟",
    ],
    "💰 أسعار مقارنة": [
        "إيه أرخص مسكن؟", "إيه أغلى دواء؟", "إيه أحسن سعر؟",
        "فولتارين أغلى من بنادول؟", "إيه الفرق في السعر؟",
    ],
    # ─── البدائل ───
    "🔄 بدائل مباشرة": [
        "بديل البنادول", "بدائل الفولتارين", "إيه ينفع بدل البروفين؟",
    ],
    "🔄 بدائل صعبة": [
        "عايز حاجة زي البنادول بس أرخص",
        "إيه اللي ينفع للألم بدل الفولتارين؟",
        "بدائل طبيعية للأسبرين",
        "في حاجة متوفرة أكتر من الأموكسيسيلين؟",
        "عايز بديل بنفس المفعول بس أقل أعراض جانبية",
    ],
    # ─── الأعراض ───
    "🩺 أعراض بسيطة": [
        "عندي صداع", "حاسس بألم في المعدة", "عندي حرارة",
        "كحة", "زكام", "ألم في الحلق", "رشح", "ألم في الظهر",
        "شد عضلي", "أرق", "قلق", "إسهال", "إمساك", "قيء",
    ],
    "🩺 أعراض متوسطة": [
        "صداع مزمن", "ألم في المفاصل", "حساسية موسمية",
        "التهاب في الحلق", "برد قوي", "ألم في الأسنان",
        "ألم في الأذن", "حرقة في المعدة", "انتفاخ",
    ],
    "🚨 حالات حرجة": [
        "عندي ألم في صدري", "ضيق في التنفس", "نزيف حاد",
        "فقدت الوعي", "تشنجات", "شلل في نصف الجسم",
        "ألم في الرأس مفاجئ", "قيء مع دم", "دم في البول",
        "ألم شديد في البطن", "حرارة 40", "إغماء",
    ],
    # ─── أسئلة صعبة ───
    "🤔 أسئلة غامضة": [
        "عايز حاجة", "محتاج دوا", "في إيه عندكم؟",
        "إيه أحسن دواء؟", "قولي حاجة تنفع", "عايز حاجة كويسة",
        "إيه اللي بتشتغل بيه؟", "إيه الجديد؟",
    ],
    "🤔 أسئلة فلسفية": [
        "إيه معنى الصحة؟", "هل الدوا دايماً هو الحل؟",
        "إمتى أشوف دكتور؟", "إيه أحسن طريقة للوقاية؟",
    ],
    # ─── لغات ───
    "🔀 خلط لغات بسيط": [
        "عايز Panadol", "إيه سعر Paracetamol؟", "بديل Voltaren",
    ],
    "🔀 خلط لغات معقد": [
        "I need something for headache بالعربي",
        "what about the سعر of Panadol?",
        "عايز حاجة like Ibuprofen بس أرخص",
        "إيه الـ dosage of Paracetamol?",
        "أنا عندي headache و fever",
    ],
    "🌍 لغات تانية": [
        "hello", "مرحبا", "bonjour", "أهلاً",
    ],
    # ─── خارج النطاق ───
    "❓ خارج النطاق تماماً": [
        "الطقس عامل إيه؟", "مين رئيس مصر؟", "إيه أحسن مطعم؟",
        "اسمع أغنية", "قولي نكتة", "إيه عاصمة فرنسا؟",
        "احسبلي 5+7", "translate this",
    ],
    "❓ خارج النطاق لكن قريب": [
        "إيه أحسن دكتور؟", "إيه أحسن مستشفى؟",
        "فين أقرب صيدلية؟", "إيه أحسن تأمين صحي؟",
    ],
    # ─── حالات طبية دقيقة ───
    "🧪 حالات طبية خاصة": [
        "أنا حامل، إيه المسكن الآمن؟",
        "عندي سكري، ينفع البنادول؟",
        "عندي ضغط، إيه الأدوية اللي أتجنبها؟",
        "عندي قرحة، إيه المسكن الآمن؟",
        "بأرضع، ينفع الفولتارين؟",
        "عندي فشل كلوي، إيه المسكن الآمن؟",
        "عندي حساسية من البنسلين",
        "عندي ربو، ينفع البروفين؟",
    ],
    "🧪 جرعات الأطفال": [
        "ابني 3 سنين، جرعة البنادول؟",
        "طفل 5 سنين، إيه المسكن؟",
        "رضيع 6 شهور، فيه دوا للحرارة؟",
        "ابني عنده 10 سنين، جرعة البروفين؟",
    ],
    # ─── متعددة ───
    "🎯 حالات مركبة": [
        "عندي صداع وحرارة وكحة",
        "محتاج مضاد حيوي ومسكن",
        "عايز حاجة للبرد والزكام",
        "عندي ألم في المعدة وصداع",
        "حاسس بتعب وقلقان وعايز حاجة",
        "عايز حاجة تنوم وتخفف الألم",
        "عندي حساسية وكحة وحرارة",
    ],
    # ─── تفاصيل ───
    "🔬 أسئلة عن التفاصيل": [
        "إيه المادة الفعالة في البنادول؟",
        "إيه شكل الفولتارين؟",
        "إيه جرعة البروفين للبالغين؟",
        "إيه أعراض الأموكسيسيلين الجانبية؟",
        "البنادول يحتاج روشتة؟",
        "الفولتارين يجي إيه أحجام؟",
        "إيه لون علبة البنادول؟",
        "إيه الشركة المصنعة؟",
    ],
    # ─── مقارنات ───
    "⚖️ مقارنات": [
        "البنادول أحسن ولا البروفين؟",
        "إيه الفرق بين البنادول والبروفين؟",
        "إيه أحسن مسكن، البنادول ولا الأسبرين؟",
        "الكونجستال أحسن ولا التلفاست؟",
        "إيه الفرق بين الأموكسيسيلين والأزيثرومايسين؟",
        "البنادول العادي أحسن ولا الإكسترا؟",
    ],
    # ─── وقت الاستخدام ───
    "⏰ حالات الاستخدام": [
        "إمتى أاخد البروفين؟",
        "ينفع أشرب الأسبرين على معدة فاضية؟",
        "إيه أحسن وقت للفيتامين؟",
        "أاخد المضاد الحيوي قبل الأكل ولا بعده؟",
        "ينفع أشرب الدوا مع اللبن؟",
        "ينفع أشرب الدوا مع القهوة؟",
    ],
    # ─── خدمات ───
    "🚚 خدمات الصيدلية": [
        "عندكم توصيل؟", "مواعيد العمل إيه؟", "العنوان فين؟",
        "عايز أطلب توصيل", "في خدمة 24 ساعة؟",
        "بتاخدوا كاش ولا كارت؟", "في خصم؟",
    ],
    # ─── أوردرات ───
    "🛒 أوردرات": [
        "عايز أطلب بنادول", "عايز أطلب توصيل",
        "تتبع الأوردر", "عايز ألغي طلبي",
        "متى هيوصل؟", "إيه رسوم التوصيل؟",
    ],
    # ─── سلبيات ───
    "😤 حالات سلبية": [
        "الدواء اللي أخدته فشل",
        "عايز شكوى",
        "عندي استفسار بس",
        "مش لاقي اللي عايزه",
        "الأدوية غالية أوي",
        "خدمتكم وحشة",
        "اتأخرتوا في التوصيل",
    ],
    # ─── أسئلة متسلسلة ───
    "🔗 أسئلة متسلسلة (Context)": [
        "بنادول|بكام؟|بديله إيه؟|ينفع للحامل؟",
        "فولتارين|إيه جرعته؟|فيه أعراض جانبية؟|بديله إيه؟",
        "عندي صداع|إيه اللي ينفع؟|بكام؟|فيه توصيل؟",
    ],
    # ─── أسئلة طويلة ───
    "📝 أسئلة طويلة": [
        "السلام عليكم ورحمة الله وبركاته، أنا عايز أسأل حضرتك عن دواء للصداع يكون آمن وسعره مناسب ومتوفر عندكم",
        "صباح الخير، عندي سؤال بخصوص الأدوية اللي بتصرف بدون روشتة، إيه أحسن حاجة للألم الخفيف؟",
        "أنا عندي مشكلة في النوم، هل فيه دوا طبيعي ينفع من غير أعراض جانبية؟",
    ],
    # ─── أسئلة قصيرة ───
    "⚡ أسئلة قصيرة": [
        "بنادول", "بكام", "بديل", "صداع", "حرارة", "دوا", "عايز",
    ],
    # ─── تكرار ───
    "🔁 أسئلة مكررة": [
        "بنادول", "بنادول", "بنادول", "بنادول", "بنادول",
    ],
    # ─── أسئلة بكلمات مفتاحية ───
    "🔑 أسئلة بكلمات مفتاحية": [
        "أرخص مسكن", "أقوى مسكن", "أسرع مسكن", "أفضل مضاد",
        "أحسن دوا للحرارة", "أقوى دوا للألم",
    ],
}

PHARMACY_TESTS = {
    "⭐ اقتراح ردود متنوعة": [
        "اقترح رد على عميل بيسأل عن دواء للصداع",
        "عميل بيسأل بكام البنادول",
        "عميل عايز يعرف بديل الفولتارين",
        "عميل بيسأل عن دواء للحساسية",
        "عميل عنده صداع مزمن",
        "عميل بيسأل عن فيتامينات",
        "عميل عايز مضاد حيوي بدون روشتة",
        "عميل غاضب لأن الدوا غالي",
        "عميل مستعجل وعايز حاجة سريعة",
        "عميل مش عارف يوصف أعراضه",
    ],
    "💊 معلومات دواء متقدمة": [
        "إيه جرعة البنادول القصوى في اليوم؟",
        "الأموكسيسيلين آمن للحوامل؟",
        "الأعراض الجانبية للفولتارين على المدى الطويل",
        "إيه التداخلات بين الفولتارين والضغط؟",
        "إيه أحسن مسكن لمريض الكلى؟",
        "الأسبرين للأطفال فيه خطر؟",
        "إيه أحسن مضاد حيوي لالتهاب الحلق؟",
        "إيه أحسن دوا للحساسية بدون نعاس؟",
    ],
    "⚠️ تداخلات دوائية": [
        "الباراسيتامول مع الوارفارين",
        "الفولتارين مع الأسبرين",
        "الأموكسيسيلين مع مانع الحمل",
        "الكونجستال مع البروفين",
        "الميتفورمين مع الأسبرين",
    ],
    "📊 إحصائيات الصيدلية": [
        "إحصائياتي النهاردة", "كام عميل جالي؟",
        "إيه أكتر دواء مطلوب؟", "إيه أفضل يوم في الأسبوع؟",
        "إيه أوقات الذروة؟",
    ],
    "🎯 حالات عمل": [
        "عايز أعمل تقرير مبيعات",
        "إزاي أحسن خدمة العملاء",
        "إزاي أتعامل مع عميل غاضب",
        "إزاي أزود المبيعات",
    ],
}

ADMIN_TESTS = {
    "📊 إحصائيات المنصة": [
        "إحصائيات المنصة", "كام صيدلية على المنصة؟",
        "إيه أكتر دواء مطلوب؟", "كام مستخدم مسجل؟",
        "إيه أعلى صيدلية استخداماً؟", "متوسط الاستخدام اليومي كام؟",
        "كام محادثة النهاردة؟", "إيه أكتر سؤال بيتكرر؟",
    ],
    "🛠️ تقني": [
        "حالة الخدمات", "صحة النظام", "مشاكل النظام",
        "إيه اللي محتاج تحسين؟", "حالة الـ DB",
        "حالة WhatsApp service", "كام request في الثانية؟",
        "إيه أبطأ endpoint؟",
    ],
    "📱 واتساب": [
        "جلسات واتساب", "حالة الـ WhatsApp",
        "مشاكل في واتساب", "كام رسالة اتبعتت؟",
    ],
    "🕐 نشاط": [
        "آخر 10 طلبات", "الطلبات الفاشلة",
        "الطلبات البطيئة", "متوسط الاستجابة",
        "إيه اللي حصل النهاردة؟",
    ],
    "📈 تحليلات": [
        "تحليلات الاستخدام", "إحصائيات الأخطاء",
        "إحصائيات المحادثات", "متوسط جودة الردود",
        "إيه أكتر وقت ازدحام؟",
    ],
    "🎯 عمليات": [
        "restart whatsapp", "restart api", "امسح اللوجات",
    ],
}


# ═══════════════════════════════════════════════════════════════════
# تحليل متعدد المستويات
# ═══════════════════════════════════════════════════════════════════
def deep_analyze(question: str, reply: str, tools: List[str], duration_ms: int) -> dict:
    """تحليل عميق للرد."""
    analysis = {}

    # 1. الطول
    analysis["length"] = len(reply)
    analysis["words"] = len(reply.split())
    analysis["lines"] = len(reply.split("\n"))

    # 2. المحتوى
    analysis["has_emoji"] = bool(re.search(r'[\U0001F300-\U0001F9FF]', reply))
    analysis["has_price"] = bool(re.search(r'\d+\s*(ج|جنيه|EGP)', reply))
    analysis["has_bullets"] = "•" in reply or "- " in reply
    analysis["has_bold"] = "**" in reply
    analysis["has_arabic"] = bool(re.search(r'[\u0600-\u06FF]', reply))
    analysis["has_english"] = bool(re.search(r'[a-zA-Z]{3,}', reply))

    # 3. الأخطاء
    analysis["has_error"] = any(x in reply for x in [
        "مشكلة", "خطأ", "فشل", "حاول تاني", "معلش",
        "غير متاح", "مش لاقي", "internal", "exception",
    ])
    analysis["is_empty"] = len(reply.strip()) < 10

    # 4. الأدوات
    analysis["has_tools"] = len(tools) > 0
    analysis["tools"] = tools

    # 5. السرعة
    analysis["duration_ms"] = duration_ms
    analysis["is_slow"] = duration_ms > 5000

    # 6. الأسئلة الحرجة
    critical_keywords = ["ألم في صدري", "ضيق تنفس", "نزيف", "فقدت الوعي", "شلل", "قيء مع دم"]
    analysis["is_critical"] = any(k in question for k in critical_keywords)

    if analysis["is_critical"]:
        # لو الحالة حرجة، لازم يكون الرد فيه تحذير طبي
        analysis["handled_critical"] = any(x in reply for x in [
            "طبيب", "مستشفى", "إسعاف", "طوارئ", "فوراً", "⚠️", "🚨",
        ])
    else:
        analysis["handled_critical"] = True

    # 7. حساب الـ Score
    score = 0
    if not analysis["has_error"]: score += 25
    if not analysis["is_empty"]: score += 15
    if analysis["words"] > 10: score += 10
    if analysis["words"] > 30: score += 10
    if analysis["has_tools"]: score += 15
    if analysis["has_price"]: score += 5
    if analysis["has_emoji"]: score += 5
    if analysis["has_bullets"]: score += 5
    if analysis["has_bold"]: score += 5
    if analysis["handled_critical"]: score += 5
    if not analysis["is_slow"]: score += 5

    analysis["score"] = min(score, 100)
    analysis["verdict"] = (
        "🟢 ممتاز" if score >= 85 else
        "🟢 جيد جداً" if score >= 70 else
        "🟡 جيد" if score >= 50 else
        "🟠 مقبول" if score >= 30 else
        "🔴 ضعيف"
    )

    return analysis


# ═══════════════════════════════════════════════════════════════════
# Test Runner
# ═══════════════════════════════════════════════════════════════════
async def run_single_test(role: str, category: str, question: str) -> dict:
    """يشغّل اختبار واحد."""
    from chatbot.roles.orchestrator import route_message

    start = time.time()
    try:
        result = await route_message(
            role=role,
            message=question,
            context={
                "user_id": f"test_{role}_{random.randint(1, 1000)}",
                "pharmacy_id": f"test_pharmacy_{random.randint(1, 10)}",
                "phone": f"+2010000{random.randint(10000, 99999)}",
            },
        )
        duration_ms = int((time.time() - start) * 1000)

        reply = result.get("reply", "")
        tools = result.get("tools_used", [])

        analysis = deep_analyze(question, reply, tools, duration_ms)

        return {
            "role": role,
            "category": category,
            "question": question,
            "reply": reply,
            "tools": tools,
            "duration_ms": duration_ms,
            "analysis": analysis,
            "success": True,
        }
    except Exception as e:
        return {
            "role": role,
            "category": category,
            "question": question,
            "error": str(e)[:300],
            "duration_ms": int((time.time() - start) * 1000),
            "success": False,
        }


async def run_multi_turn_test(role: str, conversation: List[str]) -> dict:
    """يشغّل اختبار متعدد اللفات."""
    from chatbot.roles.orchestrator import route_message

    session_id = f"test_session_{random.randint(10000, 99999)}"
    turns = []

    for i, question in enumerate(conversation):
        start = time.time()
        try:
            result = await route_message(
                role=role,
                message=question,
                context={
                    "user_id": f"test_{role}_user",
                    "session_id": session_id,
                },
            )
            duration_ms = int((time.time() - start) * 1000)
            turns.append({
                "turn": i + 1,
                "question": question,
                "reply": result.get("reply", "")[:200],
                "duration_ms": duration_ms,
            })
        except Exception as e:
            turns.append({
                "turn": i + 1,
                "question": question,
                "error": str(e)[:200],
            })

    return {
        "role": role,
        "conversation": conversation,
        "turns": turns,
        "total_turns": len(turns),
        "success": True,
    }


async def run_all_tests():
    """يشغّل كل الاختبارات."""
    results = {"customer": [], "pharmacy": [], "admin": []}
    multi_turn_results = []

    # حساب الإجمالي
    total_cust = sum(len(v) for v in CUSTOMER_TESTS.values())
    total_pharm = sum(len(v) for v in PHARMACY_TESTS.values())
    total_admin = sum(len(v) for v in ADMIN_TESTS.values())
    grand_total = total_cust + total_pharm + total_admin

    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " 💀💀💀 H1-AI Chatbot — ULTIMATE BRUTAL TEST ".center(78) + "║")
    print("║" + f" {grand_total} سؤال × {len(CUSTOMER_TESTS)+len(PHARMACY_TESTS)+len(ADMIN_TESTS)} فئة × تقييم 12 معيار ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")

    print(f"📊 الإجمالي:")
    print(f"   👤 Customer: {total_cust} سؤال في {len(CUSTOMER_TESTS)} فئة")
    print(f"   🏪 Pharmacy: {total_pharm} سؤال في {len(PHARMACY_TESTS)} فئة")
    print(f"   👑 Admin: {total_admin} سؤال في {len(ADMIN_TESTS)} فئة")
    print(f"   🔗 Multi-turn: 3 محادثات متعددة\n")

    global_counter = 0
    start_time = time.time()

    # ─── Customer Tests ───
    print("═" * 80)
    print("👤 CUSTOMER TESTS")
    print("═" * 80)

    for category, questions in CUSTOMER_TESTS.items():
        if any("|" in q for q in questions):
            continue  # skip multi-turn here

        print(f"\n▶ {category} ({len(questions)} سؤال)")
        print("─" * 80)

        for q in questions:
            global_counter += 1
            result = await run_single_test("customer", category, q)
            results["customer"].append(result)

            if result["success"]:
                a = result["analysis"]
                print(f"  [{global_counter:03d}/{grand_total}] {a['verdict']} {q[:45]}")
                print(f"       → {result['reply'][:130]}")
                if result["tools"]:
                    print(f"       🔧 {result['tools']}")
                print(f"       ⏱️  {result['duration_ms']}ms | {a['words']} كلمة | Score: {a['score']}/100")
            else:
                print(f"  [{global_counter:03d}/{grand_total}] ❌ {q[:45]}")
                print(f"       Error: {result.get('error', '')[:150]}")
            print()

    # ─── Pharmacy Tests ───
    print("\n" + "═" * 80)
    print("🏪 PHARMACY TESTS")
    print("═" * 80)

    for category, questions in PHARMACY_TESTS.items():
        print(f"\n▶ {category} ({len(questions)} سؤال)")
        print("─" * 80)

        for q in questions:
            global_counter += 1
            result = await run_single_test("pharmacy", category, q)
            results["pharmacy"].append(result)

            if result["success"]:
                a = result["analysis"]
                print(f"  [{global_counter:03d}/{grand_total}] {a['verdict']} {q[:45]}")
                print(f"       → {result['reply'][:130]}")
                if result["tools"]:
                    print(f"       🔧 {result['tools']}")
                print(f"       ⏱️  {result['duration_ms']}ms | {a['words']} كلمة | Score: {a['score']}/100")
            else:
                print(f"  [{global_counter:03d}/{grand_total}] ❌ {q[:45]}")
                print(f"       Error: {result.get('error', '')[:150]}")
            print()

    # ─── Admin Tests ───
    print("\n" + "═" * 80)
    print("👑 ADMIN TESTS")
    print("═" * 80)

    for category, questions in ADMIN_TESTS.items():
        print(f"\n▶ {category} ({len(questions)} سؤال)")
        print("─" * 80)

        for q in questions:
            global_counter += 1
            result = await run_single_test("admin", category, q)
            results["admin"].append(result)

            if result["success"]:
                a = result["analysis"]
                print(f"  [{global_counter:03d}/{grand_total}] {a['verdict']} {q[:45]}")
                print(f"       → {result['reply'][:130]}")
                if result["tools"]:
                    print(f"       🔧 {result['tools']}")
                print(f"       ⏱️  {result['duration_ms']}ms | {a['words']} كلمة | Score: {a['score']}/100")
            else:
                print(f"  [{global_counter:03d}/{grand_total}] ❌ {q[:45]}")
                print(f"       Error: {result.get('error', '')[:150]}")
            print()

    # ─── Multi-turn Tests ───
    print("\n" + "═" * 80)
    print("🔗 MULTI-TURN TESTS (Context Awareness)")
    print("═" * 80)

    multi_turn_convs = [
        ["بنادول", "بكام؟", "بديله إيه؟", "ينفع للحامل؟", "شكراً"],
        ["فولتارين", "إيه جرعته؟", "فيه أعراض جانبية؟", "بديله إيه؟"],
        ["عندي صداع", "إيه اللي ينفع؟", "بكام؟", "فيه توصيل؟"],
    ]

    for i, conv in enumerate(multi_turn_convs, 1):
        print(f"\n▶ محادثة {i}: {' → '.join(conv)}")
        result = await run_multi_turn_test("customer", conv)
        multi_turn_results.append(result)

        for turn in result["turns"]:
            if "error" in turn:
                print(f"  Turn {turn['turn']}: ❌ {turn.get('question', '')[:30]} — {turn['error'][:80]}")
            else:
                print(f"  Turn {turn['turn']}: {turn['question'][:30]}")
                print(f"           → {turn['reply'][:100]}")
                print(f"           ⏱️  {turn['duration_ms']}ms")
        print()

    # ─── Summary ───
    total_duration = time.time() - start_time

    print("\n" + "═" * 80)
    print("📊 FINAL SUMMARY")
    print("═" * 80)

    grand_success = 0
    grand_failed = 0
    grand_errors = 0
    grand_slow = 0

    for role in ["customer", "pharmacy", "admin"]:
        tests = results[role]
        if not tests:
            continue

        successful = [t for t in tests if t["success"]]
        failed = [t for t in tests if not t["success"]]
        errors = [t for t in successful if t["analysis"]["has_error"]]
        slow = [t for t in successful if t["analysis"]["is_slow"]]

        durations = [t["duration_ms"] for t in successful]
        avg_dur = sum(durations) / max(len(durations), 1)
        p50 = sorted(durations)[len(durations) // 2] if durations else 0
        p95 = sorted(durations)[int(len(durations) * 0.95)] if durations else 0
        p99 = sorted(durations)[int(len(durations) * 0.99)] if durations else 0
        max_dur = max(durations) if durations else 0

        scores = [t["analysis"]["score"] for t in successful]
        avg_score = sum(scores) / max(len(scores), 1)

        words = [t["analysis"]["words"] for t in successful]
        avg_words = sum(words) / max(len(words), 1)

        with_price = len([t for t in successful if t["analysis"]["has_price"]])
        with_emoji = len([t for t in successful if t["analysis"]["has_emoji"]])
        critical_handled = len([t for t in successful if t["analysis"].get("is_critical") and t["analysis"].get("handled_critical")])
        critical_total = len([t for t in successful if t["analysis"].get("is_critical")])

        grand_success += len(successful)
        grand_failed += len(failed)
        grand_errors += len(errors)
        grand_slow += len(slow)

        print(f"\n{'='*30}")
        print(f"  {role.upper()}")
        print(f"{'='*30}")
        print(f"  📊 Total: {len(tests)}")
        print(f"  ✅ Success: {len(successful)} ({len(successful)*100//max(len(tests),1)}%)")
        print(f"  ❌ Failed: {len(failed)}")
        print(f"  ⚠️  Errors: {len(errors)} ({len(errors)*100//max(len(successful),1)}%)")
        print(f"  🐌 Slow (>5s): {len(slow)}")
        print(f"  ⏱️  Timing: avg={avg_dur:.0f}ms | p50={p50}ms | p95={p95}ms | p99={p99}ms | max={max_dur}ms")
        print(f"  📝 Avg words: {avg_words:.1f}")
        print(f"  🎯 Avg score: {avg_score:.1f}/100")
        print(f"  💰 With price: {with_price}")
        print(f"  😊 With emoji: {with_emoji}")
        print(f"  🚨 Critical handled: {critical_handled}/{critical_total}")

        if errors:
            print(f"\n  🔴 Top errors:")
           cd ~/h1-ai/backend && source ~/venvs/h1-ai-backend/bin/activate && \
echo "═══ 1. إنشاء صيدليات افتراضية ═══" && \
python3 << 'PYEOF'
from db import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    # نتأكد من الأعمدة
    cols = db.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'pharmacies'
        ORDER BY ordinal_position
    """)).fetchall()
    print("📋 أعمدة pharmacies:")
    for c in cols:
        print(f"   {c.column_name:<25} {c.data_type:<20} {c.is_nullable}")

    # نضيف الصيدليات الافتراضية
    test_pharmacies = [
        ("test_pharmacy_1", "صيدلية اختبار 1"),
        ("test_pharmacy_2", "صيدلية اختبار 2"),
        ("test_pharmacy_3", "صيدلية اختبار 3"),
        ("test_pharmacy_4", "صيدلية اختبار 4"),
        ("test_pharmacy_5", "صيدلية اختبار 5"),
        ("test_pharmacy", "صيدلية اختبار"),
        ("default", "الصيدلية الافتراضية"),
    ]

    for pid, name in test_pharmacies:
        try:
            # نجرب نضيف بالـ id بس الأول
            db.execute(text("""
                INSERT INTO pharmacies (id, name, phone, is_active, created_at, updated_at)
                VALUES (:id, :name, :phone, true, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {"id": pid, "name": name, "phone": "+201000000000"})
            db.commit()
            print(f"   ✅ {pid}")
        except Exception as e:
            db.rollback()
            # نجرب بدون updated_at
            try:
                db.execute(text("""
                    INSERT INTO pharmacies (id, name, phone, is_active)
                    VALUES (:id, :name, :phone, true)
                    ON CONFLICT (id) DO NOTHING
                """), {"id": pid, "name": name, "phone": "+201000000000"})
                db.commit()
                print(f"   ✅ {pid} (no dates)")
            except Exception as e2:
                db.rollback()
                print(f"   ❌ {pid}: {str(e2)[:100]}")

    print()
    count = db.execute(text("SELECT COUNT(*) FROM pharmacies")).scalar()
    print(f"📊 إجمالي الصيدليات: {count}")
finally:
    db.close()
