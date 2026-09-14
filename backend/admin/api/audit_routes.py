from fastapi import APIRouter, Depends, Query
from auth.dependencies import require_admin
from auth.models import User
from admin.services.audit_service import audit_service
from admin.services.backup_service import backup_service

router = APIRouter(prefix="/v1/admin/audit", tags=["admin-audit"])


@router.get("/log")
async def get_audit_log(
    limit: int = Query(100, ge=1, le=1000),
    user: User = Depends(require_admin),
):
    return audit_service.read_recent(limit=limit)


@router.get("/backups")
async def list_backups(
    file_pattern: str = "",
    user: User = Depends(require_admin),
):
    return backup_service.list_backups(file_pattern=file_pattern)


@router.post("/backups/create")
async def create_backup(user: User = Depends(require_admin)):
    backed = backup_service.backup_all()
    return {"success": True, "backed_up": backed}
