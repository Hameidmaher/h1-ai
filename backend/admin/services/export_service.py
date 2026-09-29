"""Export Service — CSV, JSON, Excel."""
from __future__ import annotations
import csv
import io
import json
from typing import Any
import structlog
from admin.services.crud_service import crud_service

logger = structlog.get_logger()


class ExportService:
    def products_csv(self) -> str:
        products = crud_service.list_products(skip=0, limit=100000)
        if not products:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)
        return output.getvalue()

    def products_json(self) -> str:
        products = crud_service.list_products(skip=0, limit=100000)
        return json.dumps(products, ensure_ascii=False, indent=2)

    def drugs_json(self) -> str:
        return json.dumps(
            crud_service.list_drugs(), ensure_ascii=False, indent=2,
        )

    def interactions_json(self) -> str:
        return json.dumps(
            crud_service.list_interactions(), ensure_ascii=False, indent=2,
        )

    def full_backup(self) -> dict[str, Any]:
        return {
            "products": crud_service.list_products(skip=0, limit=100000),
            "drugs": crud_service.list_drugs(),
            "conditions": crud_service.list_conditions(),
            "interactions": crud_service.list_interactions(),
            "synonyms": crud_service.list_synonyms(),
            "stats": crud_service.get_stats(),
        }


export_service = ExportService()
