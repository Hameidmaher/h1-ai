from __future__ import annotations
from dataclasses import dataclass
from knowledge.analyzer.normalizer import normalizer
from knowledge.analyzer.ner import ner, NERResult


@dataclass
class AnalyzedQuery:
    original: str
    normalized: str
    tokens: list[str]
    entities: NERResult
    intent: str = "unknown"
    language: str = "ar"
    has_emergency: bool = False
    needs_prescription: bool = False


EMERGENCY_KEYS = [
    "الم في الصدر", "وجع في الصدر", "سكته", "مخنوق",
    "مش قادر اتنفس", "ضيق تنفس", "شلل", "تسمم"
]

PRESCRIPTION_KEYS = [
    "روشته", "وصفه طبيه", "بوصفه", "prescription"
]


class QueryAnalyzer:
    def analyze(self, query: str) -> AnalyzedQuery:
        n = normalizer.normalize(query)
        tokens = normalizer.tokenize(query)
        entities = ner.extract(query)
        has_emergency = any(k in n for k in EMERGENCY_KEYS)
        needs_prescription = any(k in n for k in PRESCRIPTION_KEYS)
        return AnalyzedQuery(
            original=query, normalized=n, tokens=tokens,
            entities=entities,
            intent=self._intent(n, entities),
            has_emergency=has_emergency,
            needs_prescription=needs_prescription,
        )

    def _intent(self, n: str, entities: NERResult) -> str:
        if any(k in n for k in ["سعر", "بكام"]):
            return "price_query"
        if any(k in n for k in ["متوفر", "موجود"]):
            return "stock_query"
        if entities.symptoms or entities.conditions:
            return "medical_advice"
        if entities.drugs:
            return "product_query"
        return "general"


query_analyzer = QueryAnalyzer()
