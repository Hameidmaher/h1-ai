"""Import Service — CSV, JSON, Excel."""
from __future__ import annotations
import structlog
from admin.services.crud_service import crud_service

logger = structlog.get_logger()


class ImportService:
    def import_products(self, rows: list[dict]) -> dict:
        created = 0
        errors = []
        for i, row in enumerate(rows):
            try:
                crud_service.create_product({
                    "item_code": row.get("item_code") or row.get("ItemCode"),
                    "name": row.get("name") or row.get("ItemName"),
                    "category": row.get("category") or row.get("Category"),
                    "price": float(row.get("price") or row.get("Price", 0)),
                    "stock_qty": int(row.get("stock_qty") or row.get("StockQty", 0)),
                    "expiry_date": row.get("expiry_date") or row.get("ExpiryDate"),
                    "description": row.get("description") or row.get("Description", ""),
                })
                created += 1
            except Exception as e:
                errors.append({"row": i, "error": str(e)})
        return {"created": created, "errors": errors}

    def import_drugs(self, drugs: dict) -> dict:
        created = 0
        errors = []
        for drug_id, data in drugs.items():
            try:
                crud_service.create_drug(drug_id, data)
                created += 1
            except Exception as e:
                errors.append({"drug": drug_id, "error": str(e)})
        return {"created": created, "errors": errors}

    def import_interactions(self, items: list[dict]) -> dict:
        created = 0
        errors = []
        for i, item in enumerate(items):
            try:
                crud_service.create_interaction(item)
                created += 1
            except Exception as e:
                errors.append({"row": i, "error": str(e)})
        return {"created": created, "errors": errors}


import_service = ImportService()
