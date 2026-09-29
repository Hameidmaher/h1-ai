from __future__ import annotations
from rapidfuzz import fuzz, process
from knowledge.analyzer.normalizer import normalizer
from knowledge.loader import knowledge_loader
import structlog

logger = structlog.get_logger()


class FuzzyIndex:
    def __init__(self, threshold: int = 70, max_results: int = 5):
        self.threshold = threshold
        self.max_results = max_results
        self.names: list[str] = []
        self.originals: list[str] = []
        self._built = False

    def build(self) -> None:
        if self._built:
            return
        for p in knowledge_loader.products:
            name = p.get("ItemName", "")
            if name:
                self.names.append(normalizer.normalize(name))
                self.originals.append(name)
        self._built = True

    def search(self, query: str) -> list[tuple[str, float]]:
        if not self._built:
            self.build()
        if not self.names:
            return []
        nq = normalizer.normalize(query)
        if not nq:
            return []
        matches = process.extract(nq, self.names, scorer=fuzz.WRatio,
                                   limit=self.max_results, score_cutoff=self.threshold)
        return [(self.originals[i], s) for _, s, i in matches]


fuzzy_index = FuzzyIndex()
