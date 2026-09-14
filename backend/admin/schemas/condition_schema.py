from pydantic import BaseModel, Field
from typing import Optional


class ConditionCreate(BaseModel):
    id: str = Field(min_length=2, max_length=50)
    display_name: str = Field(min_length=1, max_length=200)
    keywords: dict[str, list[str]] = Field(default_factory=dict)
    first_line: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    avoid: list[dict] = Field(default_factory=list)


class ConditionUpdate(BaseModel):
    display_name: Optional[str] = None
    keywords: Optional[dict[str, list[str]]] = None
    first_line: Optional[list[str]] = None
    alternatives: Optional[list[str]] = None
    warnings: Optional[list[str]] = None
    avoid: Optional[list[dict]] = None
