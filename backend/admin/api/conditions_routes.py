from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import require_admin
from auth.models import User
from admin.schemas.condition_schema import (
    ConditionCreate, ConditionUpdate,
)
from admin.services.crud_service import crud_service
from admin.services.audit_service import audit_service
from admin.services.backup_service import backup_service

router = APIRouter(
    prefix="/v1/admin/conditions", tags=["admin-conditions"],
)


@router.get("")
async def list_conditions(user: User = Depends(require_admin)):
    return crud_service.list_conditions()


@router.post("", status_code=201)
async def create_condition(
    req: ConditionCreate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("medical_rules.yaml")
    data = req.model_dump()
    cond_id = data.pop("id")
    entry = crud_service.create_condition(cond_id, data)
    audit_service.log(
        user=user.username, action="CREATE",
        entity="condition", entity_id=cond_id,
    )
    return {"success": True, "data": entry}


@router.put("/{cond_id}")
async def update_condition(
    cond_id: str,
    req: ConditionUpdate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("medical_rules.yaml")
    updated = crud_service.update_condition(
        cond_id, req.model_dump(exclude_none=True),
    )
    if not updated:
        raise HTTPException(404, "Condition not found")
    audit_service.log(
        user=user.username, action="UPDATE",
        entity="condition", entity_id=cond_id,
    )
    return {"success": True, "data": updated}


@router.delete("/{cond_id}")
async def delete_condition(
    cond_id: str,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("medical_rules.yaml")
    deleted = crud_service.delete_condition(cond_id)
    if not deleted:
        raise HTTPException(404, "Condition not found")
    audit_service.log(
        user=user.username, action="DELETE",
        entity="condition", entity_id=cond_id,
    )
    return {"success": True}
