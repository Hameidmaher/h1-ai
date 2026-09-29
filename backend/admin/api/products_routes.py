from fastapi import APIRouter, Depends, HTTPException, Query
from auth.dependencies import require_admin
from auth.models import User
from admin.schemas.product_schema import (
    ProductCreate, ProductUpdate,
)
from admin.schemas.common_schema import (
    BulkDeleteRequest, SuccessResponse, PaginatedResponse, StatsResponse,
)
from admin.services.crud_service import crud_service
from admin.services.audit_service import audit_service
from admin.services.backup_service import backup_service
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin/products", tags=["admin-products"])


@router.get("", response_model=PaginatedResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: User = Depends(require_admin),
):
    total = crud_service.count_products()
    skip = (page - 1) * page_size
    items = crud_service.list_products(skip=skip, limit=page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/stats", response_model=StatsResponse)
async def get_stats(user: User = Depends(require_admin)):
    return crud_service.get_stats()


@router.get("/{item_code}")
async def get_product(
    item_code: str,
    user: User = Depends(require_admin),
):
    product = crud_service.get_product(item_code)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.post("", response_model=SuccessResponse, status_code=201)
async def create_product(
    req: ProductCreate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("products.csv")
    data = req.model_dump()
    product = crud_service.create_product(data)
    audit_service.log(
        user=user.username, action="CREATE",
        entity="product", entity_id=product["ItemCode"],
    )
    return {"success": True, "message": "Product created", "data": product}


@router.put("/{item_code}")
async def update_product(
    item_code: str,
    req: ProductUpdate,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("products.csv")
    updated = crud_service.update_product(item_code, req.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(404, "Product not found")
    audit_service.log(
        user=user.username, action="UPDATE",
        entity="product", entity_id=item_code,
    )
    return {"success": True, "data": updated}


@router.delete("/{item_code}")
async def delete_product(
    item_code: str,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("products.csv")
    deleted = crud_service.delete_product(item_code)
    if not deleted:
        raise HTTPException(404, "Product not found")
    audit_service.log(
        user=user.username, action="DELETE",
        entity="product", entity_id=item_code,
    )
    return {"success": True, "message": "Product deleted"}


@router.post("/bulk-delete")
async def bulk_delete(
    req: BulkDeleteRequest,
    user: User = Depends(require_admin),
):
    backup_service.backup_file("products.csv")
    count = crud_service.bulk_delete_products(req.ids)
    audit_service.log(
        user=user.username, action="BULK_DELETE",
        entity="product", details={"count": count},
    )
    return {"success": True, "deleted": count}
