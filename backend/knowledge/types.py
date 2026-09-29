from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Product:
    item_code: str
    name: str
    category: str
    price: float
    stock_qty: int
    expiry_date: str
    description: str = ""


@dataclass
class Warning:
    level: Literal["info", "warning", "danger", "emergency"]
    message: str
    reason: str = ""


@dataclass
class Interaction:
    drug1: str
    drug2: str
    severity: Literal["minor", "moderate", "major"]
    effect: str
    action: str


@dataclass
class Emergency:
    detected: bool = False
    type: str = ""
    message: str = ""
    emergency_number: str = ""
    severity: str = "critical"


@dataclass
class AdvisoryResult:
    query: str = ""
    confidence: float = 0.0
    method: str = "default"
    products: list[Product] = field(default_factory=list)
    advice: str = ""
    conditions: list[str] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    interactions: list[Interaction] = field(default_factory=list)
    emergency: Emergency = field(default_factory=lambda: Emergency(detected=False))
    follow_ups: list[str] = field(default_factory=list)
    has_direct_answer: bool = False
    needs_prescription: bool = False
    needs_human: bool = False
    is_emergency: bool = False
    sources: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "confidence": self.confidence,
            "method": self.method,
            "products": [
                {"item_code": p.item_code, "name": p.name, "price": p.price,
                 "stock_qty": p.stock_qty, "category": p.category}
                for p in self.products
            ],
            "advice": self.advice,
            "conditions": self.conditions,
            "warnings": [{"level": w.level, "message": w.message} for w in self.warnings],
            "alternatives": self.alternatives,
            "interactions": [{"drug1": i.drug1, "drug2": i.drug2,
                              "severity": i.severity, "effect": i.effect}
                             for i in self.interactions],
            "emergency": {"detected": self.emergency.detected,
                          "type": self.emergency.type,
                          "message": self.emergency.message},
            "follow_ups": self.follow_ups,
            "has_direct_answer": self.has_direct_answer,
            "needs_prescription": self.needs_prescription,
            "needs_human": self.needs_human,
            "is_emergency": self.is_emergency,
            "sources": self.sources,
            "explanation": self.explanation,
        }
