from pydantic import BaseModel, Field
from typing import Optional


class DrugCreate(BaseModel):
    id: str = Field(min_length=2, max_length=50)
    name_ar: str = Field(min_length=1, max_length=200)
    name_en: str = Field(min_length=1, max_length=200)
    aliases: list[str] = Field(default_factory=list)
    drug_class: str = Field(default="", alias="class")
    indications: list[str] = Field(default_factory=list)
    safe_pregnancy: bool = True
    safe_children: bool = True
    max_daily_mg: int = 0
    notes: str = ""

    model_config = {"populate_by_name": True}


class DrugUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    aliases: Optional[list[str]] = None
    drug_class: Optional[str] = Field(None, alias="class")
    indications: Optional[list[str]] = None
    safe_pregnancy: Optional[bool] = None
    safe_children: Optional[bool] = None
    max_daily_mg: Optional[int] = None
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}
