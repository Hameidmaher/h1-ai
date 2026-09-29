from __future__ import annotations
from typing import Optional
from rank_bm25 import BM25Okapi
from knowledge.analyzer.normalizer import normalizer
from knowledge.loader import knowledge_loader
import structlog

logger = structlog.get_logger()


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.tokenized: list[list[str]] = []
        self.products: list[dict] = []
        self.bm25: Optional[BM25Okapi] = None
        self._built = False

    def build(self) -> None:
        if self._built:
            return
        for p in knowledge_loader.products:
            text = f"{p.get('ItemName', '')} {p.get('Category', '')} {p.get('Description', '')}"
            self.tokenized.append(normalizer.tokenize(text))
            self.products.append(p)
        if self.tokenized:
            self.bm25 = BM25Okapi(self.tokenized, k1=self.k1, b=self.b)
            self._built = True
            logger.info("bm25.built", size=len(self.products))

    def search(self, query: str, top_k: int = 10) -> list[tuple[dict, float]]:
        if not self._built or not self.bm25:
            return []
        tokens = normalizer.tokenize(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)
        return [(self.products[i], float(s)) for i, s in indexed[:top_k] if s > 0]


bm25_index = BM25Index()
