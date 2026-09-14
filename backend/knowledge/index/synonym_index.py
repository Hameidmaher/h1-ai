from __future__ import annotations
from knowledge.analyzer.normalizer import normalizer
from knowledge.loader import knowledge_loader
import structlog

logger = structlog.get_logger()


class SynonymIndex:
    def __init__(self):
        self.synonyms: dict[str, list[str]] = {}
        self.dialect_map: dict[str, str] = {}
        self._built = False

    def build(self) -> None:
        if self._built:
            return
        data = knowledge_loader.synonyms
        for k, vals in data.get("synonyms", {}).items():
            self.synonyms[normalizer.normalize(k)] = [normalizer.normalize(v) for v in vals]
        for k, v in data.get("egyptian_dialect", {}).items():
            self.dialect_map[normalizer.normalize(k)] = normalizer.normalize(v)
        self._built = True

    def expand(self, query: str) -> list[str]:
        if not self._built:
            self.build()
        n = normalizer.normalize(query)
        expanded = {n}
        for token in n.split():
            for sk, sv in self.synonyms.items():
                if token in sk or sk in token:
                    for v in sv:
                        expanded.add(v)
        return list(expanded)


synonym_index = SynonymIndex()
