from __future__ import annotations
import re
import unicodedata


class ArabicNormalizer:
    ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06DC]")

    def normalize(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFKC", text)
        text = text.lower()
        text = self.ARABIC_DIACRITICS.sub("", text)
        text = text.replace("\u0640", "")
        text = re.sub(r"[\u0623\u0625\u0622\u0671]", "\u0627", text)
        text = re.sub(r"\u0649", "\u064A", text)
        text = re.sub(r"\u0629", "\u0647", text)
        text = re.sub(r"\u0626", "\u064A", text)
        text = re.sub(r"\u0624", "\u0648", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text: str) -> list[str]:
        n = self.normalize(text)
        if not n:
            return []
        cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", n)
        return [t for t in cleaned.split() if len(t) >= 2]


normalizer = ArabicNormalizer()
