from __future__ import annotations
from dataclasses import dataclass, field
from knowledge.loader import knowledge_loader
from knowledge.analyzer.normalizer import normalizer
import structlog

logger = structlog.get_logger()


@dataclass
class Entity:
    text: str
    type: str
    normalized: str = ""
    confidence: float = 1.0


@dataclass
class NERResult:
    entities: list[Entity] = field(default_factory=list)
    drugs: list[str] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    demographics: list[str] = field(default_factory=list)


class RuleBasedNER:
    def __init__(self):
        self._drugs: dict[str, str] = {}
        self._symptoms: dict[str, str] = {}
        self._conditions: dict[str, str] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        for drug_id, info in knowledge_loader.drugs.items():
            self._drugs[drug_id] = drug_id
            for key in ["name_ar", "name_en"]:
                val = info.get(key, "")
                if val:
                    self._drugs[normalizer.normalize(val)] = drug_id
            for alias in info.get("aliases", []):
                self._drugs[normalizer.normalize(alias)] = drug_id

        for sym_id, info in knowledge_loader.symptoms.items():
            self._symptoms[sym_id] = sym_id
            val = info.get("name_ar", "")
            if val:
                self._symptoms[normalizer.normalize(val)] = sym_id

        conditions = knowledge_loader.medical_rules.get("conditions", {})
        for cond_id, info in conditions.items():
            self._conditions[cond_id] = cond_id
            display = info.get("display_name", "")
            if display:
                self._conditions[normalizer.normalize(display)] = cond_id
            for lang_kws in info.get("keywords", {}).values():
                if isinstance(lang_kws, list):
                    for k in lang_kws:
                        self._conditions[normalizer.normalize(k)] = cond_id

        self._loaded = True

    def extract(self, text: str) -> NERResult:
        self._load()
        result = NERResult()
        ntext = normalizer.normalize(text)
        tokens = ntext.split()
        for token in tokens:
            if token in self._drugs and self._drugs[token] not in result.drugs:
                result.drugs.append(self._drugs[token])
            if token in self._symptoms and self._symptoms[token] not in result.symptoms:
                result.symptoms.append(self._symptoms[token])
            if token in self._conditions and self._conditions[token] not in result.conditions:
                result.conditions.append(self._conditions[token])
        for ckw, cid in self._conditions.items():
            if len(ckw) >= 3 and ckw in ntext and cid not in result.conditions:
                result.conditions.append(cid)
        return result


ner = RuleBasedNER()
