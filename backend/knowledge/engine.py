"""Advisory Engine — Advanced with Rules + Fusion + Synonym Expansion."""
from __future__ import annotations
from knowledge.types import (
    AdvisoryResult, Product, Warning, Interaction, Emergency,
)
from knowledge.loader import knowledge_loader
from knowledge.analyzer.query_analyzer import query_analyzer
from knowledge.analyzer.normalizer import normalizer
from knowledge.index.bm25_index import bm25_index
from knowledge.index.fuzzy_index import fuzzy_index
from knowledge.index.synonym_index import synonym_index
import structlog

logger = structlog.get_logger()


class AdvisoryEngine:
    def __init__(self):
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        knowledge_loader.load_all()
        bm25_index.build()
        fuzzy_index.build()
        synonym_index.build()
        self._initialized = True
        logger.info("advisory.initialized")

    # ═══════════════════════════════════════════════════════
    # SEARCH (with synonym expansion)
    # ═══════════════════════════════════════════════════════
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._initialized:
            self.initialize()

        # 1. توسيع المرادفات
        expanded = synonym_index.expand(query)
        logger.debug("search.expanded", original=query, expanded=expanded[:3])

        # 2. البحث بكل صيغة + دمج النتائج
        all_results: dict[str, tuple[dict, float]] = {}
        for q in expanded:
            for product, score in bm25_index.search(q, top_k=top_k):
                code = str(product.get("ItemCode", ""))
                if code not in all_results or score > all_results[code][1]:
                    all_results[code] = (product, score)

        # 3. ترتيب + إرجاع
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x[1],
            reverse=True,
        )
        return [p for p, _ in sorted_results[:top_k]]

    # ═══════════════════════════════════════════════════════
    # EMERGENCY DETECTION
    # ═══════════════════════════════════════════════════════
    def _detect_emergency(self, text: str) -> Emergency:
        rules = knowledge_loader.medical_rules
        emergencies = rules.get("emergencies", {})
        if not emergencies:
            return Emergency(detected=False)

        ntext = normalizer.normalize(text)
        logger.debug("emergency.check", normalized=ntext[:80])

        for em_type, info in emergencies.items():
            keywords = info.get("keywords", {})
            all_kws = []
            for lang_list in keywords.values():
                if isinstance(lang_list, list):
                    all_kws.extend(lang_list)

            for kw in all_kws:
                nkw = normalizer.normalize(kw)
                if nkw and nkw in ntext:
                    logger.warning(
                        "emergency.detected",
                        type=em_type, keyword=kw,
                    )
                    return Emergency(
                        detected=True,
                        type=em_type,
                        message=info.get("message", ""),
                        emergency_number=info.get("emergency_number", "123"),
                    )
        return Emergency(detected=False)

    # ═══════════════════════════════════════════════════════
    # INTERACTIONS
    # ═══════════════════════════════════════════════════════
    def _check_interactions(self, drugs: list[str]) -> list[Interaction]:
        results = []
        for i in knowledge_loader.interactions:
            d1 = i.get("drug1", "")
            d2 = i.get("drug2", "")
            if d1 in drugs and d2 in drugs:
                results.append(Interaction(
                    drug1=d1, drug2=d2,
                    severity=i.get("severity", "minor"),
                    effect=i.get("effect", ""),
                    action=i.get("action", ""),
                ))
        return results

    # ═══════════════════════════════════════════════════════
    # CONDITION RULES
    # ═══════════════════════════════════════════════════════
    def _apply_condition_rules(
        self, conditions: list[str]
    ) -> tuple[str, list[Warning]]:
        rules = knowledge_loader.medical_rules.get("conditions", {})
        advice_parts = []
        warnings = []

        for cond in conditions:
            info = rules.get(cond)
            if not info:
                continue
            name = info.get("display_name", cond)
            first_line = info.get("first_line", [])
            if first_line:
                advice_parts.append(
                    f"لـ{name}: الخيارات الأولى هي {', '.join(first_line[:3])}"
                )
            for w in info.get("warnings", []):
                warnings.append(Warning(level="warning", message=w))
            for avoid in info.get("avoid", []):
                if isinstance(avoid, dict):
                    warnings.append(Warning(
                        level="danger",
                        message=f"تجنّب {avoid.get('name')}: {avoid.get('reason')}",
                    ))

        return " | ".join(advice_parts), warnings


    def _conditions_to_products(
        self, conditions: list[str]
    ) -> list[Product]:
        """
        يحوّل conditions إلى منتجات محددة من المخزون.
        مثال: "headache" -> ["paracetamol", "ibuprofen"] -> [Paracetamol 500mg, Ibuprofen 400mg]
        """
        rules = knowledge_loader.medical_rules.get("conditions", {})
        product_names: set[str] = set()

        for cond in conditions:
            info = rules.get(cond, {})
            for drug in info.get("first_line", []):
                product_names.add(drug.lower())
            for alt in info.get("alternatives", []):
                product_names.add(alt.lower())

        if not product_names:
            return []

        products: list[Product] = []
        for p in knowledge_loader.products:
            name = p.get("ItemName", "").lower()
            for pname in product_names:
                if pname in name:
                    products.append(Product(
                        item_code=str(p.get("ItemCode", "")),
                        name=p.get("ItemName", ""),
                        category=p.get("Category", ""),
                        price=float(p.get("Price", 0)),
                        stock_qty=int(p.get("StockQty", 0)),
                        expiry_date=p.get("ExpiryDate", ""),
                        description=p.get("Description", ""),
                    ))
                    break
        return products

    # ═══════════════════════════════════════════════════════
    # ANALYZE (main entry point)
    # ═══════════════════════════════════════════════════════
    def analyze(self, query: str) -> AdvisoryResult:
        if not self._initialized:
            self.initialize()

        logger.info("analyze.start", query=query[:80])

        analyzed = query_analyzer.analyze(query)

        # 1. Emergency check
        emergency = self._detect_emergency(query)
        if emergency.detected:
            return AdvisoryResult(
                query=query,
                confidence=1.0,
                method="emergency",
                emergency=emergency,
                is_emergency=True,
                needs_human=True,
                has_direct_answer=True,
                advice=emergency.message,
                sources=["emergency"],
            )

        # 2. Search (with synonym expansion)
        expanded = synonym_index.expand(query)
        all_search: dict[str, tuple[dict, float]] = {}
        for q in expanded:
            for product, score in bm25_index.search(q, top_k=5):
                code = str(product.get("ItemCode", ""))
                if code not in all_search or score > all_search[code][1]:
                    all_search[code] = (product, score)

        sorted_search = sorted(
            all_search.values(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        products = [
            Product(
                item_code=str(p.get("ItemCode", "")),
                name=p.get("ItemName", ""),
                category=p.get("Category", ""),
                price=float(p.get("Price", 0)),
                stock_qty=int(p.get("StockQty", 0)),
                expiry_date=p.get("ExpiryDate", ""),
                description=p.get("Description", ""),
            )
            for p, _ in sorted_search
        ]

        # 3. Condition rules
        advice_text, warnings = self._apply_condition_rules(
            analyzed.entities.conditions
        )

        # 3b. Condition -> Products
        condition_products = self._conditions_to_products(
            analyzed.entities.conditions
        )
        existing_codes = {p.item_code for p in products}
        for cp in condition_products:
            if cp.item_code not in existing_codes:
                products.append(cp)
                existing_codes.add(cp.item_code)

        # 4. Interactions
        interactions = self._check_interactions(analyzed.entities.drugs)
        for inter in interactions:
            level = "danger" if inter.severity == "major" else "warning"
            warnings.append(Warning(
                level=level,
                message=f"تداخل {inter.severity}: {inter.effect}",
            ))

        # 5. Confidence
        confidence = 0.3
        if products:
            confidence = min(0.95, 0.4 + len(products) * 0.1)
        if analyzed.entities.conditions:
            confidence = min(0.95, confidence + 0.2)
        if analyzed.entities.drugs:
            confidence = min(0.95, confidence + 0.15)

        logger.info(
            "analyze.done",
            products=len(products),
            conditions=analyzed.entities.conditions,
            drugs=analyzed.entities.drugs,
            confidence=round(confidence, 2),
        )

        return AdvisoryResult(
            query=query,
            confidence=confidence,
            method="bm25+rules",
            products=products,
            advice=advice_text,
            warnings=warnings,
            interactions=interactions,
            has_direct_answer=bool(products) or bool(advice_text),
            needs_prescription=analyzed.needs_prescription,
            sources=["bm25", "rules"],
        )


advisory_engine = AdvisoryEngine()
