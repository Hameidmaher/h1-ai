from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import csv
import io
import json
from auth.dependencies import require_admin
from auth.models import User
from admin.services.import_service import import_service
from admin.services.audit_service import audit_service
from admin.services.backup_service import backup_service

router = APIRouter(prefix="/v1/admin/import", tags=["admin-import"])


@router.post("/products/csv")
async def import_products_csv(
    file: UploadFile = File(...),
    user: User = Depends(require_admin),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "File must be CSV")
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    backup_service.backup_file("products.csv")
    result = import_service.import_products(rows)
    audit_service.log(
        user=user.username, action="IMPORT",
        entity="product", details={"count": result["created"]},
    )
    return result


@router.post("/drugs/json")
async def import_drugs_json(
    file: UploadFile = File(...),
    user: User = Depends(require_admin),
):
    content = await file.read()
    data = json.loads(content.decode("utf-8"))
    drugs = data.get("drugs", data)
    backup_service.backup_file("drugs.json")
    result = import_service.import_drugs(drugs)
    audit_service.log(
        user=user.username, action="IMPORT",
        entity="drug", details={"count": result["created"]},
    )
    return result
