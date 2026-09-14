from pydantic import BaseModel, Field
from typing import Optional, Any


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(min_length=1)


class ImportRequest(BaseModel):
    data: list[dict[str, Any]]
    mode: str = "append"


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    products_count: int
    drugs_count: int
    conditions_count: int
    interactions_count: int
    synonyms_count: int
    low_stock_count: int
    expiring_soon_count: int
