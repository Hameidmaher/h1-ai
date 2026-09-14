from typing import Literal
from dataclasses import dataclass
from knowledge.engine import advisory_engine
import structlog

logger = structlog.get_logger()


STRONG_PHARMACIST_KEYWORDS = [
    "تداخل دوائي", "تفاعل دوائي", "جرعة",
    "مخزون", "نفاد", "صلاحية", "انتهاء صلاحية",
    "روشتة", "وصفة طبية", "مراجعة وصفة", "تقرير",
]

AMBIGUOUS_SIGNALS = ["بدائل", "بديل"]

STRICT_PHARMACIST_SIGNALS = [
    "اعمل لي", "اعملي", "راجع", "مراجعة",
    "قائمة بكل", "كود المنتج", "تحقق من", "في المخزن",
]


@dataclass
class RouteResult:
    user_type: Literal["customer", "pharmacist"]
    confidence: float
    method: Literal["keyword", "ambiguous", "advisory", "default"]


class Router:
    def route(self, message: str) -> RouteResult:
        msg = message.strip().lower()

        # 1) Advisory check أولاً
        try:
            adv = advisory_engine.analyze(message)
            if adv.needs_prescription:
                return RouteResult("pharmacist", 0.95, "advisory")
        except Exception:
            pass

        # 2) STRONG keywords
        for kw in STRONG_PHARMACIST_KEYWORDS:
            if kw in msg:
                return RouteResult("pharmacist", 0.95, "keyword")

        # 3) AMBIGUOUS
        if any(s in msg for s in AMBIGUOUS_SIGNALS):
            if any(s in msg for s in STRICT_PHARMACIST_SIGNALS):
                return RouteResult("pharmacist", 0.85, "ambiguous")
            return RouteResult("customer", 0.7, "ambiguous")

        return RouteResult("customer", 0.7, "default")

    def route_type(self, message: str) -> str:
        return self.route(message).user_type
