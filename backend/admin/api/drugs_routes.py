from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import require_admin
from auth.models import User
from admin.schemas.drug_schema import DrugCreate, DrugUpdate
from admin.services.crud_service import crud_service
from admin.services.audit_service import audit_service
from admin.services.backup_service import backup_service

router = APIRouter(prefix="/v1/admin/drugs", tags=["admin-drugs"])


@router.get("")
async def list_drugs(user: User = Depends(require_admin)):
    return crud_service.list_drugs()


@router.get("/{drug_id}")
async def get_drug(drug_id: str, user: User = Depends(require_admin)):
    drugs = crud_service.list_drugs()
    if drug_id not in drugs:
        raise HTTPException(404, "Drug not found")
    return drugs[drug_id]


@router.post("", status_code=201)
async def create_drug(
    req: DrugCreate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("drugs.json")
    data = req.model_dump(by_alias=True)
    drug_id = data.pop("id")
    entry = crud_service.create_drug(drug_id, data)
    audit_service.log(
        user=user.username, action="CREATE",
        entity="drug", entity_id=drug_id,
    )
    return {"success": True, "data": entry}


@router.put("/{drug_id}")
async def update_drug(
    drug_id: str,
    req: DrugUpdate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("drugs.json")
    updated = crud_service.update_drug(
        drug_id, req.model_dump(by_alias=True, exclude_none=True),
    )
    if not updated:
        raise HTTPException(404, "Drug not found")
    audit_service.log(
        user=user.username, action="UPDATE",
        entity="drug", entity_id=drug_id,
    )
    return {"success": True, "data": updated}


@router.delete("/{drug_id}")
async def delete_drug(
    drug_id: str,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("drugs.json")
    deleted = crud_service.delete_drug(drug_id)
    if not deleted:
        raise HTTPException(404, "Drug not found")
    audit_service.log(
        user=user.username, action="DELETE",
        entity="drug", entity_id=drug_id,
    )
    return {"success": True}
