"""Generic CRUD Service — يعمل على كل الجداول."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Optional
import yaml
import structlog

logger = structlog.get_logger()


class CRUDService:
    """يدير CRUD لملفات CSV/JSON/YAML."""

    def __init__(self, data_dir: str = "../data"):
        self.data_dir = Path(data_dir)

    # ──────── Products (CSV) ────────
    def _read_products(self) -> list[dict]:
        path = self.data_dir / "products.csv"
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _write_products(self, products: list[dict]) -> None:
        path = self.data_dir / "products.csv"
        if not products:
            return
        fields = [
            "ItemCode", "ItemName", "Category", "Price",
            "StockQty", "ExpiryDate", "Description",
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(products)

    def list_products(self, skip: int = 0, limit: int = 100) -> list[dict]:
        products = self._read_products()
        return products[skip:skip + limit]

    def count_products(self) -> int:
        return len(self._read_products())

    def get_product(self, item_code: str) -> Optional[dict]:
        for p in self._read_products():
            if str(p.get("ItemCode")) == str(item_code):
                return p
        return None

    def create_product(self, data: dict) -> dict:
        products = self._read_products()
        # Auto-generate item_code if not given
        if not data.get("item_code"):
            codes = [int(p["ItemCode"]) for p in products if p.get("ItemCode", "").isdigit()]
            new_code = str(max(codes) + 1) if codes else "1001"
            data["item_code"] = new_code
        row = {
            "ItemCode": str(data["item_code"]),
            "ItemName": data["name"],
            "Category": data["category"],
            "Price": str(data["price"]),
            "StockQty": str(data["stock_qty"]),
            "ExpiryDate": data["expiry_date"],
            "Description": data.get("description", ""),
        }
        products.append(row)
        self._write_products(products)
        return row

    def update_product(self, item_code: str, data: dict) -> Optional[dict]:
        products = self._read_products()
        updated = None
        for i, p in enumerate(products):
            if str(p.get("ItemCode")) == str(item_code):
                if data.get("name"):
                    p["ItemName"] = data["name"]
                if data.get("category"):
                    p["Category"] = data["category"]
                if data.get("price") is not None:
                    p["Price"] = str(data["price"])
                if data.get("stock_qty") is not None:
                    p["StockQty"] = str(data["stock_qty"])
                if data.get("expiry_date"):
                    p["ExpiryDate"] = data["expiry_date"]
                if data.get("description") is not None:
                    p["Description"] = data["description"]
                products[i] = p
                updated = p
                break
        if updated:
            self._write_products(products)
        return updated

    def delete_product(self, item_code: str) -> bool:
        products = self._read_products()
        filtered = [p for p in products if str(p.get("ItemCode")) != str(item_code)]
        if len(filtered) == len(products):
            return False
        self._write_products(filtered)
        return True

    def bulk_delete_products(self, item_codes: list[str]) -> int:
        codes_set = {str(c) for c in item_codes}
        products = self._read_products()
        filtered = [p for p in products if str(p.get("ItemCode")) not in codes_set]
        deleted = len(products) - len(filtered)
        self._write_products(filtered)
        return deleted

    # ──────── Drugs (JSON) ────────
    def _read_json(self, name: str, key: str) -> dict:
        path = self.data_dir / name
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f).get(key, {})

    def _write_json(self, name: str, key: str, data: dict) -> None:
        path = self.data_dir / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": "1.0", key: data}, f, ensure_ascii=False, indent=2)

    def list_drugs(self) -> dict:
        return self._read_json("drugs.json", "drugs")

    def create_drug(self, drug_id: str, data: dict) -> dict:
        drugs = self.list_drugs()
        entry = {
            "name_ar": data.get("name_ar", ""),
            "name_en": data.get("name_en", ""),
            "aliases": data.get("aliases", []),
            "class": data.get("class", data.get("drug_class", "")),
            "indications": data.get("indications", []),
            "safe_pregnancy": data.get("safe_pregnancy", True),
            "safe_children": data.get("safe_children", True),
            "max_daily_mg": data.get("max_daily_mg", 0),
        }
        drugs[drug_id] = entry
        self._write_json("drugs.json", "drugs", drugs)
        return entry

    def update_drug(self, drug_id: str, data: dict) -> Optional[dict]:
        drugs = self.list_drugs()
        if drug_id not in drugs:
            return None
        for k, v in data.items():
            if v is not None:
                drugs[drug_id][k] = v
        self._write_json("drugs.json", "drugs", drugs)
        return drugs[drug_id]

    def delete_drug(self, drug_id: str) -> bool:
        drugs = self.list_drugs()
        if drug_id not in drugs:
            return False
        del drugs[drug_id]
        self._write_json("drugs.json", "drugs", drugs)
        return True

    # ──────── Interactions ────────
    def _read_interactions(self) -> list[dict]:
        path = self.data_dir / "interactions.json"
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("interactions", [])

    def _write_interactions(self, data: list[dict]) -> None:
        path = self.data_dir / "interactions.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"version": "1.0", "interactions": data},
                f, ensure_ascii=False, indent=2,
            )

    def list_interactions(self) -> list[dict]:
        return self._read_interactions()

    def create_interaction(self, data: dict) -> dict:
        items = self._read_interactions()
        new_item = {
            "drug1": data["drug1"],
            "drug2": data["drug2"],
            "severity": data.get("severity", "moderate"),
            "effect": data["effect"],
            "action": data["action"],
        }
        items.append(new_item)
        self._write_interactions(items)
        return new_item

    def update_interaction(self, index: int, data: dict) -> Optional[dict]:
        items = self._read_interactions()
        if index < 0 or index >= len(items):
            return None
        for k, v in data.items():
            if v is not None:
                items[index][k] = v
        self._write_interactions(items)
        return items[index]

    def delete_interaction(self, index: int) -> bool:
        items = self._read_interactions()
        if index < 0 or index >= len(items):
            return False
        del items[index]
        self._write_interactions(items)
        return True

    # ──────── Synonyms ────────
    def _read_synonyms(self) -> dict:
        path = self.data_dir / "synonyms_ar.json"
        if not path.exists():
            return {"synonyms": {}, "egyptian_dialect": {}}
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_synonyms(self, data: dict) -> None:
        path = self.data_dir / "synonyms_ar.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_synonyms(self) -> dict:
        return self._read_synonyms()

    def add_synonym(self, term: str, synonyms: list[str]) -> dict:
        data = self._read_synonyms()
        data.setdefault("synonyms", {})
        existing = data["synonyms"].get(term, [])
        merged = list(set(existing + synonyms))
        data["synonyms"][term] = merged
        self._write_synonyms(data)
        return {"term": term, "synonyms": merged}

    def delete_synonym(self, term: str) -> bool:
        data = self._read_synonyms()
        if term not in data.get("synonyms", {}):
            return False
        del data["synonyms"][term]
        self._write_synonyms(data)
        return True

    # ──────── Conditions (YAML) ────────
    def _read_rules(self) -> dict:
        path = self.data_dir / "medical_rules.yaml"
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write_rules(self, data: dict) -> None:
        path = self.data_dir / "medical_rules.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    def list_conditions(self) -> dict:
        return self._read_rules().get("conditions", {})

    def create_condition(self, cond_id: str, data: dict) -> dict:
        rules = self._read_rules()
        rules.setdefault("conditions", {})
        entry = {
            "display_name": data.get("display_name", cond_id),
            "keywords": data.get("keywords", {}),
            "first_line": data.get("first_line", []),
            "alternatives": data.get("alternatives", []),
            "warnings": data.get("warnings", []),
            "avoid": data.get("avoid", []),
        }
        rules["conditions"][cond_id] = entry
        self._write_rules(rules)
        return entry

    def update_condition(self, cond_id: str, data: dict) -> Optional[dict]:
        rules = self._read_rules()
        conds = rules.get("conditions", {})
        if cond_id not in conds:
            return None
        for k, v in data.items():
            if v is not None:
                conds[cond_id][k] = v
        self._write_rules(rules)
        return conds[cond_id]

    def delete_condition(self, cond_id: str) -> bool:
        rules = self._read_rules()
        conds = rules.get("conditions", {})
        if cond_id not in conds:
            return False
        del conds[cond_id]
        self._write_rules(rules)
        return True

    # ──────── Stats ────────
    def get_stats(self) -> dict:
        from datetime import datetime, timedelta
        products = self._read_products()
        low_stock = [p for p in products if int(p.get("StockQty", 0)) < 10]
        cutoff = datetime.now() + timedelta(days=90)
        expiring = 0
        for p in products:
            try:
                exp = datetime.strptime(p.get("ExpiryDate", ""), "%Y-%m-%d")
                if exp <= cutoff:
                    expiring += 1
            except Exception:
                continue
        return {
            "products_count": len(products),
            "drugs_count": len(self.list_drugs()),
            "conditions_count": len(self.list_conditions()),
            "interactions_count": len(self._read_interactions()),
            "synonyms_count": len(self._read_synonyms().get("synonyms", {})),
            "low_stock_count": len(low_stock),
            "expiring_soon_count": expiring,
        }


crud_service = CRUDService()
