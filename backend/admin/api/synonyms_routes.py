from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import require_admin
from auth.models import User
from admin.schemas.synonym_schema import SynonymCreate, DialectCreate
from admin.services.crud_service import crud_service
from admin.services.audit_service import audit_service
from admin.services.backup_service import backup_service

router = APIRouter(prefix="/v1/admin/synonyms", tags=["admin-synonyms"])


@router.get("")
async def list_synonyms(user: User = Depends(require_admin)):
    return crud_service.list_synonyms()


@router.post("", status_code=201)
async def add_synonym(
    req: SynonymCreate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("synonyms_ar.json")
    entry = crud_service.add_synonym(req.term, req.synonyms)
    audit_service.log(
        user=user.username, action="CREATE",
        entity="synonym", entity_id=req.term,
    )
    return {"success": True, "data": entry}


@router.delete("/{term}")
async def delete_synonym(
    term: str,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("synonyms_ar.json")
    deleted = crud_service.delete_synonym(term)
    if not deleted:
        raise HTTPException(404, "Synonym not found")
    audit_service.log(
        user=user.username, action="DELETE",
        entity="synonym", entity_id=term,
    )
    return {"success": True}
