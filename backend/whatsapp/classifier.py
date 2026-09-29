"""
تصنيف الرسائل: عميل | مورد | غامض | spam | طوارئ
"""
from dataclasses import dataclass, field
from typing import Literal

from whatsapp.keywords import (
    SUPPLIER_KEYWORDS,
    CUSTOMER_KEYWORDS,
    URGENT_PATTERNS,
    BLACKLIST_PATTERNS,
    normalize_text,
)
import structlog

logger = structlog.get_logger()


ClassificationType = Literal[
    "customer", "supplier", "unknown", "spam", "urgent"
]


@dataclass
class Classification:
    type: ClassificationType
    confidence: float
    supplier_score: int = 0
    customer_score: int = 0
    matched_supplier: list[str] = field(default_factory=list)
    matched_customer: list[str] = field(default_factory=list)
    reason: str = ""


class MessageClassifier:
    """
    يصنّف الرسائل بناءً على:
    1. Blacklist (spam) → تجاهل
    2. Urgent (طوارئ) → رد فوري
    3. Supplier keywords
    4. Customer keywords
    5. الحساب النهائي
    """

    # عتبات القرار
    SUPPLIER_THRESHOLD = 5      # ≥ 5 → مورد
    CUSTOMER_THRESHOLD = 3      # ≥ 4 → عميل
    CONFIDENT_RATIO = 2.0        # النسبة بين الطرفين

    def classify(self, text: str) -> Classification:
        if not text or not text.strip():
            return Classification(
                type="unknown",
                confidence=0.0,
                reason="empty_message",
            )

        normalized = normalize_text(text)

        # ═══ 1. Blacklist (spam) ═══
        for pattern in BLACKLIST_PATTERNS:
            if normalize_text(pattern) in normalized:
                logger.info(
                    "classifier.spam_detected",
                    pattern=pattern,
                )
                return Classification(
                    type="spam",
                    confidence=1.0,
                    reason=f"blacklist:{pattern}",
                )

        # ═══ 2. Urgent (طوارئ) ═══
        for pattern in URGENT_PATTERNS:
            if normalize_text(pattern) in normalized:
                logger.warning(
                    "classifier.urgent_detected",
                    pattern=pattern,
                )
                return Classification(
                    type="urgent",
                    confidence=1.0,
                    reason=f"urgent:{pattern}",
                )

        # ═══ 3. حساب درجات المورد ═══
        supplier_score = 0
        matched_supplier = []
        for kw, weight in SUPPLIER_KEYWORDS.items():
            if normalize_text(kw) in normalized:
                supplier_score += weight
                matched_supplier.append(kw)

        # ═══ 4. حساب درجات العميل ═══
        customer_score = 0
        matched_customer = []
        for kw, weight in CUSTOMER_KEYWORDS.items():
            if normalize_text(kw) in normalized:
                customer_score += weight
                matched_customer.append(kw)

        logger.debug(
            "classifier.scores",
            supplier_score=supplier_score,
            customer_score=customer_score,
            supplier_matches=matched_supplier[:5],
            customer_matches=matched_customer[:5],
        )

        # ═══ 5. القرار ═══
        return self._decide(
            supplier_score, customer_score,
            matched_supplier, matched_customer,
        )

    def _decide(
        self,
        supplier_score: int,
        customer_score: int,
        matched_supplier: list[str],
        matched_customer: list[str],
    ) -> Classification:
        """يقرر التصنيف النهائي."""

        # ═══ حالة 1: مورد واضح ═══
        if supplier_score >= self.SUPPLIER_THRESHOLD:
            # تحقق: هل العميل أقوى بكثير؟
            if customer_score >= supplier_score * 2 and customer_score >= 8:
                # عميل سأل عن مورد (مثل: "هل عندكو بانادول من مخزن ابن سينا؟")
                conf = min(customer_score / 20.0, 0.9)
                return Classification(
                    type="customer",
                    confidence=conf,
                    supplier_score=supplier_score,
                    customer_score=customer_score,
                    matched_supplier=matched_supplier,
                    matched_customer=matched_customer,
                    reason="customer_dominant",
                )

            # مورد
            conf = min(supplier_score / 15.0, 0.95)
            return Classification(
                type="supplier",
                confidence=conf,
                supplier_score=supplier_score,
                customer_score=customer_score,
                matched_supplier=matched_supplier,
                matched_customer=matched_customer,
                reason=f"supplier_score={supplier_score}",
            )

        # ═══ حالة 2: عميل واضح ═══
        if customer_score >= self.CUSTOMER_THRESHOLD:
            conf = min(customer_score / 15.0, 0.9)
            return Classification(
                type="customer",
                confidence=conf,
                supplier_score=supplier_score,
                customer_score=customer_score,
                matched_supplier=matched_supplier,
                matched_customer=matched_customer,
                reason=f"customer_score={customer_score}",
            )

        # ═══ حالة 3: غامض ═══
        return Classification(
            type="unknown",
            confidence=0.0,
            supplier_score=supplier_score,
            customer_score=customer_score,
            matched_supplier=matched_supplier,
            matched_customer=matched_customer,
            reason="no_clear_match",
        )


# Singleton
classifier = MessageClassifier()
