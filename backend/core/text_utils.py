"""
Text Utilities — Fuzzy Matching & Normalization
"""
import re


def normalize_message(message: str) -> str:
    """
    ينظف الرسالة من:
    - الحروف المكررة (سكرررر → سكر)
    - المسافات الزائدة
    - علامات الترقيم المتكررة
    """
    if not message:
        return ""

    # 1. إزالة تكرار الحروف (3+ مرات → حرف واحد)
    normalized = re.sub(r"(.)\1{2,}", r"\1", message)

    # 2. إزالة المسافات المتكررة
    normalized = re.sub(r"\s+", " ", normalized)

    # 3. إزالة علامات الترقيم المتكررة
    normalized = re.sub(r"([!؟?.,،])\1{2,}", r"\1", normalized)

    # 4. trim
    normalized = normalized.strip()

    return normalized


def should_use_normalized(original: str, normalized: str) -> bool:
    """هل نستخدم النسخة المنظفة؟"""
    if not normalized:
        return False
    if original == normalized:
        return False
    # لو التنظيف وفّر 20%+ من الطول
    if len(normalized) < len(original) * 0.8:
        return True
    return False
