"""Enhanced Classifier v2 — smart message classification.

Categories:
- urgent: emergency/health crisis (highest priority)
- spam: unsolicited ads, links, scams
- supplier: business offers, bulk orders
- customer: customer inquiries and requests
- unknown: fallback

Priority: URGENT > SPAM > SUPPLIER > CUSTOMER > unknown
"""
from __future__ import annotations
from dataclasses import dataclass, field
import re
import structlog

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════
# URGENT (emergency) keywords
# ═══════════════════════════════════════════════════════
URGENT_PHRASES = [
    # Chest pain (whole phrases only)
    "ألم في الصدر", "ألم بالصدر", "وجع في الصدر", "ضغط على الصدر",
    "ألم شديد في الصدر", "ألم في القلب",
    "chest pain", "chest pressure",
    
    # Breathing
    "صعوبة في التنفس", "صعوبة شديدة في التنفس", "مش قادر أتنفس",
    "ضيق في التنفس", "ضيق شديد في التنفس",
    "difficulty breathing", "can't breathe", "shortness of breath",
    
    # Consciousness
    "فقدان الوعي", "أغمى عليه", "مغمى عليه", "مش حاسس بنفسه",
    "غاب عن الوعي", "فاقد الوعي", "أغشي عليه",
    "loss of consciousness", "fainted", "unconscious",
    
    # Bleeding
    "نزيف حاد", "نزيف شديد", "نزيف مستمر", "دم كتير",
    "severely bleeding", "heavy bleeding",
    
    # Stroke
    "جلطة", "جلطة دماغية", "شلل مفاجئ", "تنميل في الوجه",
    "مش قادر أتكلم", "stroke", "sudden paralysis",
    
    # Emergency words
    "حالة طوارئ", "حالة عاجلة", "حالة حرجة", "حالة خطيرة",
    "emergency", "urgent", "critical",
    "فوري", "محتاج مساعدة فورية",
    
    # Allergy
    "حساسية شديدة", "تورم في الحلق", "تورم في الوجه",
    "anaphylaxis", "severe allergy",
    
    # Poisoning
    "تسمم", "جرعة زائدة", "بلع مادة سامة", "أخذ أدوية كتير",
    "poisoning", "overdose",
    
    # Seizure
    "تشنجات", "صرع", "نوبة صرع",
    "seizure", "convulsion",
]

URGENT_KEYWORDS = [
    "طوارئ", "إسعاف", "emergency",
]


# ═══════════════════════════════════════════════════════
# SPAM detection
# ═══════════════════════════════════════════════════════
SPAM_KEYWORDS = [
    # Explicit
    "spam", "scam",
    # English
    "click here", "buy now", "free money", "winner", "congratulations",
    "limited time", "act now", "earn money", "work from home",
    "crypto", "bitcoin", "investment opportunity", "guaranteed",
    "no risk", "100% free", "make money fast", "get rich",
    # Arabic
    "ربح سريع", "اربح", "جوائز", "فزت", "مبروك فزت",
    "استثمار", "بيتكوين", "عملة رقمية", "ربح مضمون",
    "اعمل من البيت", "دخل إضافي", "فرصة ذهبية",
]

SPAM_PATTERNS = [
    r"https?://\S+",       # URLs
    r"www\.\S+",           # www links
    r"(.)\1{4,}",          # Repeated chars (5+)
    r"\b\d{10,}\b",        # Long numbers
]

SPAM_MIN_SCORE = 2


# ═══════════════════════════════════════════════════════
# SUPPLIER keywords
# ═══════════════════════════════════════════════════════
SUPPLIER_KEYWORDS_WEIGHTED = {
    # High weight — explicit supplier terms
    "وارد": 3, "الوارد": 3, "كوته": 3, "كوتة": 3, "بونص": 3,
    "طلبية": 3, "توريد": 3, "فاتورة": 3, "جملة": 3, "مذكرة": 3,
    "عرض خاص": 4, "خصم جملة": 4, "سعر الجملة": 4,
    # Company names
    "ابن سينا": 5, "رامكو": 5, "نوفارتس": 5, "باير": 5, "فايزر": 5,
    "جلاكسو": 5, "سانوفي": 5, "أسترازينيكا": 5,
    # Business terms
    "شركة": 2, "مؤسسة": 2, "تجاري": 2, "business": 2,
    "wholesale": 3, "supplier": 3, "bulk order": 3,
    "عرض من": 3, "عرض من شركة": 4,
    # ═══ جديد — طلبات بالجملة ═══
    "للبيع": 4, "أبيع": 4, "بيع": 3, "للتوزيع": 4,
    "علبة": 3, "علب": 3, "كرتونة": 4, "كراتين": 4, "كارتونة": 4,
    "دستة": 3, "دستات": 3, "شوال": 4,
    "كمية كبيرة": 4, "كميات": 3,
    "بالجملة": 5, "بالجمله": 5,
    "منتج": 2, "منتجات": 2,
    # أرقام كبيرة + وحدة
    "100 علبة": 5, "200 علبة": 5, "500 علبة": 5, "1000 علبة": 5,
    "100 علب": 5, "200 علب": 5, "500 علب": 5, "1000 علب": 5,
}

SUPPLIER_MIN_SCORE = 3


# ═══════════════════════════════════════════════════════
# CUSTOMER keywords
# ═══════════════════════════════════════════════════════
CUSTOMER_KEYWORDS_WEIGHTED = {
    # Inquiries
    "عايز": 2, "عاوز": 2, "أريد": 2, "محتاج": 2, "محتاجة": 2,
    "عندكم": 2, "فيه": 1, "هل": 1, "ايه": 1, "إيه": 1,
    # Requests
    "بديل": 3, "بدائل": 3, "سعر": 2, "بكام": 3, "الثمن": 2,
    # Health
    "صداع": 2, "ألم": 2, "وجع": 2, "حرارة": 2, "كحة": 2,
    "دواء": 2, "علاج": 2,
    # Service
    "استفسار": 2, "سؤال": 1, "استفسر": 2,
    "wanted": 2, "need": 2, "looking for": 2,
    # ═══ جديد — ردود اجتماعية ═══
    "شكراً": 1, "شكرا": 1, "تسلم": 1, "تسلمي": 1,
    "تمام": 1, "ماشي": 1, "طيب": 1,
    "السلام": 1, "مرحبا": 1, "أهلاً": 1, "أهلا": 1,
    "صباح": 1, "مساء": 1,
}

CUSTOMER_MIN_SCORE = 3


# ═══════════════════════════════════════════════════════
# Classification Result
# ═══════════════════════════════════════════════════════
@dataclass
class ClassificationResult:
    type: str  # urgent | spam | supplier | customer | unknown
    confidence: float
    urgent_score: int = 0
    spam_score: int = 0
    supplier_score: int = 0
    customer_score: int = 0
    matched_urgent: list[str] = field(default_factory=list)
    matched_spam: list[str] = field(default_factory=list)
    matched_supplier: list[str] = field(default_factory=list)
    matched_customer: list[str] = field(default_factory=list)
    reason: str = ""


# ═══════════════════════════════════════════════════════
# Classifier
# ═══════════════════════════════════════════════════════
class ClassifierV2:
    """Enhanced message classifier."""
    
    def classify(self, text: str) -> ClassificationResult:
        if not text or not text.strip():
            return ClassificationResult(type="unknown", confidence=0.0, reason="empty")
        
        text_lower = text.lower()
        
        # ─── 1. URGENT (highest priority) ───
        urgent_score, urgent_matches = self._score_urgent(text_lower)
        if urgent_score >= 1:  # Just 1 phrase enough
            confidence = min(1.0, 0.7 + urgent_score * 0.1)
            logger.warning("classifier.urgent", matches=urgent_matches[:3], score=urgent_score)
            return ClassificationResult(
                type="urgent",
                confidence=confidence,
                urgent_score=urgent_score,
                matched_urgent=urgent_matches,
                reason=f"matched {len(urgent_matches)} urgent phrase(s)",
            )
        
        # ─── 2. SPAM ───
        spam_score, spam_matches = self._score_spam(text_lower, text)
        if spam_score >= SPAM_MIN_SCORE:
            confidence = min(1.0, 0.5 + spam_score * 0.1)
            logger.info("classifier.spam", score=spam_score, matches=spam_matches[:3])
            return ClassificationResult(
                type="spam",
                confidence=confidence,
                spam_score=spam_score,
                matched_spam=spam_matches,
                reason=f"spam score {spam_score}",
            )
        
        # ─── 3. SUPPLIER ───
        supplier_score, supplier_matches = self._score_supplier(text_lower)
        
        # ─── 4. CUSTOMER ───
        customer_score, customer_matches = self._score_customer(text_lower)
        
        logger.debug(
            "classifier.scores",
            supplier_score=supplier_score,
            customer_score=customer_score,
            supplier_matches=supplier_matches[:3],
            customer_matches=customer_matches[:3],
        )
        
        if supplier_score >= SUPPLIER_MIN_SCORE and supplier_score > customer_score:
            confidence = min(1.0, 0.5 + supplier_score * 0.05)
            return ClassificationResult(
                type="supplier",
                confidence=confidence,
                supplier_score=supplier_score,
                customer_score=customer_score,
                matched_supplier=supplier_matches,
                reason=f"supplier score {supplier_score} > customer {customer_score}",
            )
        
        if customer_score >= CUSTOMER_MIN_SCORE:
            confidence = min(1.0, 0.5 + customer_score * 0.05)
            return ClassificationResult(
                type="customer",
                confidence=confidence,
                supplier_score=supplier_score,
                customer_score=customer_score,
                matched_customer=customer_matches,
                reason=f"customer score {customer_score}",
            )
        
        # ─── Fallback ───
        if supplier_score > customer_score and supplier_score > 0:
            return ClassificationResult(
                type="supplier",
                confidence=0.4,
                supplier_score=supplier_score,
                customer_score=customer_score,
                matched_supplier=supplier_matches,
                reason="supplier fallback",
            )
        
        if customer_score > 0:
            return ClassificationResult(
                type="customer",
                confidence=0.4,
                supplier_score=supplier_score,
                customer_score=customer_score,
                matched_customer=customer_matches,
                reason="customer fallback",
            )
        
        return ClassificationResult(
            type="unknown",
            confidence=0.0,
            reason="no matches",
        )
    
    def _score_urgent(self, text: str) -> tuple[int, list[str]]:
        score = 0
        matches = []
        for phrase in URGENT_PHRASES:
            if phrase.lower() in text:
                matches.append(phrase)
                score += 2
        for kw in URGENT_KEYWORDS:
            if kw.lower() in text:
                matches.append(kw)
                score += 1
        return score, matches
    
    def _score_spam(self, text_lower: str, original: str) -> tuple[int, list[str]]:
        score = 0
        matches = []
        
        for kw in SPAM_KEYWORDS:
            if kw.lower() in text_lower:
                matches.append(kw)
                score += 2
        
        for pattern in SPAM_PATTERNS:
            try:
                if re.search(pattern, original):
                    matches.append(f"pattern:{pattern[:15]}")
                    score += 2
            except re.error:
                pass
        
        # Repetition check
        words = text_lower.split()
        if len(words) >= 3:
            from collections import Counter
            word_counts = Counter(words)
            most_common = word_counts.most_common(1)
            if most_common and most_common[0][1] >= 3:
                matches.append(f"repetition:{most_common[0][0]}")
                score += 3
        
        return score, matches
    
    def _score_supplier(self, text: str) -> tuple[int, list[str]]:
        score = 0
        matches = []
        for kw, weight in SUPPLIER_KEYWORDS_WEIGHTED.items():
            if kw.lower() in text:
                matches.append(kw)
                score += weight
        return score, matches
    
    def _score_customer(self, text: str) -> tuple[int, list[str]]:
        score = 0
        matches = []
        for kw, weight in CUSTOMER_KEYWORDS_WEIGHTED.items():
            if kw.lower() in text:
                matches.append(kw)
                score += weight
        return score, matches


# Singleton
classifier_v2 = ClassifierV2()
