from __future__ import annotations
import csv
import json
from pathlib import Path
import yaml
import structlog

logger = structlog.get_logger()


class KnowledgeLoader:
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = Path(data_dir)
        self.products: list[dict] = []
        self.medical_rules: dict = {}
        self.interactions: list[dict] = []
        self.synonyms: dict = {}
        self.drugs: dict = {}
        self.symptoms: dict = {}
        self.emergency_patterns: dict = {}
        self._loaded = False

    def load_all(self) -> None:
        if self._loaded:
            return
        logger.info("knowledge.loading")
        self._load_products()
        self._load_medical_rules()
        self._load_interactions()
        self._load_synonyms()
        self._load_drugs()
        self._load_symptoms()
        self._load_emergency_patterns()
        self._loaded = True
        logger.info("knowledge.loaded",
                    products=len(self.products),
                    interactions=len(self.interactions))

    def _load_products(self) -> None:
        p = self.data_dir / "products.csv"
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            self.products = list(csv.DictReader(f))

    def _load_medical_rules(self) -> None:
        p = self.data_dir / "medical_rules.yaml"
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            self.medical_rules = yaml.safe_load(f) or {}

    def _load_interactions(self) -> None:
        p = self.data_dir / "interactions.json"
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            self.interactions = json.load(f).get("interactions", [])

    def _load_synonyms(self) -> None:
        p = self.data_dir / "synonyms_ar.json"
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            self.synonyms = json.load(f)

    def _load_drugs(self) -> None:
        p = self.data_dir / "drugs.json"
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            self.drugs = json.load(f).get("drugs", {})

    def _load_symptoms(self) -> None:
        p = self.data_dir / "symptoms.json"
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            self.symptoms = json.load(f).get("symptoms", {})

    def _load_emergency_patterns(self) -> None:
        p = self.data_dir / "emergency_patterns.json"
        if not p.exists():
            return
        with open(p, encoding="utf-8") as f:
            self.emergency_patterns = json.load(f)


knowledge_loader = KnowledgeLoader()
