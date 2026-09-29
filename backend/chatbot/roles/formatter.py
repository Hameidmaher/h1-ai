"""Response Formatter — تنسيق الردود."""
from __future__ import annotations
import re


def format_response(text: str, role: str) -> dict:
    """ينسّق الرد حسب الدور."""
    if not text:
        return {"text": "—", "format": "plain"}

    # تنسيق عام
    text = _clean_whitespace(text)
    text = _normalize_emojis(text)
    text = _fix_arabic_punctuation(text)

    # تنسيق حسب الدور
    if role == "admin":
        text = _format_admin(text)
    elif role == "pharmacy":
        text = _format_pharmacy(text)
    elif role == "customer":
        text = _format_customer(text)

    return {
        "text": text,
        "format": "markdown",
        "role": role,
    }


def _clean_whitespace(text: str) -> str:
    """تنظيف الفراغات الزائدة."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _normalize_emojis(text: str) -> str:
    """توحيد الإيموجي."""
    # تبسيط الإيموجي المكررة
    text = re.sub(r'([✅❌⚠️📊💰💊🩺🔄])\1+', r'\1', text)
    return text


def _fix_arabic_punctuation(text: str) -> str:
    """تصحيح علامات الترقيم العربية."""
    # مسافة قبل علامة الاستفهام
    text = re.sub(r'(\S)\?', r'\1 ؟', text)
    # إزالة المسافات قبل الفواصل
    text = re.sub(r'\s+،', '،', text)
    text = re.sub(r'\s+\.', '.', text)
    return text


def _format_admin(text: str) -> str:
    """تنسيق للـ Admin."""
    # تأكد إن الأرقام bold
    text = re.sub(r'(\b\d+[\d,]*\b)', r'**\1**', text)
    return text


def _format_pharmacy(text: str) -> str:
    """تنسيق للـ Pharmacy."""
    # تأكد إن الأسعار bold
    text = re.sub(r'(\d+)\s*ج\b', r'**\1 ج**', text)
    text = re.sub(r'(\d+)\s*جنيه\b', r'**\1 جنيه**', text)
    return text


def _format_customer(text: str) -> str:
    """تنسيق للـ Customer."""
    # تبسيط: تقليل الأسطر الطويلة
    lines = text.split('\n')
    if len(lines) > 8:
        # اختصر
        lines = lines[:8]
        lines.append("...")
    return '\n'.join(lines)


def detect_response_type(text: str) -> str:
    """يحدد نوع الرد."""
    if not text:
        return "empty"

    # ردود الأخطاء
    if re.search(r'❌|خطأ|failed|error', text, re.IGNORECASE):
        return "error"

    # ردود النجاح
    if re.search(r'✅|نجح|تم |success', text, re.IGNORECASE):
        return "success"

    # ردود التحذير
    if re.search(r'⚠️|تحذير|warning', text, re.IGNORECASE):
        return "warning"

    # ردود البيانات (جداول/قوائم)
    if '|' in text or re.search(r'^\s*[-•*]\s', text, re.MULTILINE):
        return "data"

    return "info"
