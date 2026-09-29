"""Router — decides between customer/pharmacist based on intent.

Arabic-aware: strips "ال" definition for keyword matching.
"""
import re
from typing import Literal
from dataclasses import dataclass
from knowledge.engine import advisory_engine
import structlog

logger = structlog.get_logger()


def _normalize_arabic(text: str) -> str:
    """Strip Arabic definite article (ال) from word starts for matching."""
    return re.sub(r'\bال(?=\S)', '', text, flags=re.UNICODE)


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
    method: Literal["keyword", "ambiguous", "advisory", "default", "error"]


class Router:
    def route(self, message: str) -> RouteResult:
        if not message or not message.strip():
            return RouteResult("customer", 0.5, "default")

        msg = message.strip()

        # ─── 1. Advisory check ───
        try:
            adv = advisory_engine.analyze(message)
            if adv.needs_prescription:
                logger.info("router.advisory_prescription", msg=msg[:50])
                return RouteResult("pharmacist", 0.95, "advisory")
        except Exception as e:
            logger.warning(
                "router.advisory_failed",
                error=str(e)[:200],
                msg=msg[:50],
            )

        # ─── 2. Strong keywords (normalized) ───
        msg_norm = _normalize_arabic(msg)
        for kw in STRONG_PHARMACIST_KEYWORDS:
            kw_norm = _normalize_arabic(kw)
            if kw_norm in msg_norm:
                logger.debug(
                    "router.strong_keyword",
                    keyword=kw,
                    msg=msg[:50],
                )
                return RouteResult("pharmacist", 0.95, "keyword")

        # ─── 3. Ambiguous signals ───
        if any(s in msg for s in AMBIGUOUS_SIGNALS):
            if any(s in msg for s in STRICT_PHARMACIST_SIGNALS):
                logger.debug("router.ambiguous_pharmacist", msg=msg[:50])
                return RouteResult("pharmacist", 0.85, "ambiguous")
            logger.debug("router.ambiguous_customer", msg=msg[:50])
            return RouteResult("customer", 0.7, "ambiguous")

        # ─── 4. Default ───
        return RouteResult("customer", 0.7, "default")

    def route_type(self, message: str) -> str:
        return self.route(message).user_type


router = Router()
