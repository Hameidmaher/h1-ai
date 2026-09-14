from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, JSONResponse, Response
from auth.dependencies import require_admin
from auth.models import User
from admin.services.export_service import export_service

router = APIRouter(prefix="/v1/admin/export", tags=["admin-export"])


@router.get("/products.csv")
async def export_products_csv(user: User = Depends(require_admin)):
    content = export_service.products_csv()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.get("/products.json")
async def export_products_json(user: User = Depends(require_admin)):
    return Response(
        content=export_service.products_json(),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=products.json"},
    )


@router.get("/drugs.json")
async def export_drugs_json(user: User = Depends(require_admin)):
    return Response(
        content=export_service.drugs_json(),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=drugs.json"},
    )


@router.get("/full")
async def export_full(user: User = Depends(require_admin)):
    return export_service.full_backup()
