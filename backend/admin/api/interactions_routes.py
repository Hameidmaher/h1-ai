from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import require_admin
from auth.models import User
from admin.schemas.interaction_schema import (
    InteractionCreate, InteractionUpdate,
)
from admin.services.crud_service import crud_service
from admin.services.audit_service import audit_service
from admin.services.backup_service import backup_service

router = APIRouter(
    prefix="/v1/admin/interactions", tags=["admin-interactions"],
)


@router.get("")
async def list_interactions(user: User = Depends(require_admin)):
    return crud_service.list_interactions()


@router.post("", status_code=201)
async def create_interaction(
    req: InteractionCreate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("interactions.json")
    entry = crud_service.create_interaction(req.model_dump())
    audit_service.log(
        user=user.username, action="CREATE", entity="interaction",
    )
    return {"success": True, "data": entry}


@router.put("/{index}")
async def update_interaction(
    index: int,
    req: InteractionUpdate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("interactions.json")
    updated = crud_service.update_interaction(
        index, req.model_dump(exclude_none=True),
    )
    if not updated:
        raise HTTPException(404, "Interaction not found")
    audit_service.log(
        user=user.username, action="UPDATE", entity="interaction",
    )
    return {"success": True, "data": updated}


@router.delete("/{index}")
async def delete_interaction(
    index: int,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("interactions.json")
    deleted = crud_service.delete_interaction(index)
    if not deleted:
        raise HTTPException(404, "Interaction not found")
    audit_service.log(
        user=user.username, action="DELETE", entity="interaction",
    )
    return {"success": True}
