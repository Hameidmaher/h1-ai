from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime


class ProductCreate(BaseModel):
    item_code: Optional[str] = None
    name: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=100)
    price: float = Field(ge=0.0)
    stock_qty: int = Field(ge=0)
    expiry_date: str
    description: str = ""

    @field_validator("expiry_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("expiry_date must be YYYY-MM-DD")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    price: Optional[float] = Field(None, ge=0.0)
    stock_qty: Optional[int] = Field(None, ge=0)
    expiry_date: Optional[str] = None
    description: Optional[str] = None


class ProductResponse(BaseModel):
    item_code: str
    name: str
    category: str
    price: float
    stock_qty: int
    expiry_date: str
    description: str = ""
