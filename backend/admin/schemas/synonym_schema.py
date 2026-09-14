from pydantic import BaseModel, Field
from typing import Optional


class SynonymCreate(BaseModel):
    term: str = Field(min_length=1, max_length=100)
    synonyms: list[str] = Field(default_factory=list)


class SynonymUpdate(BaseModel):
    synonyms: Optional[list[str]] = None


class DialectCreate(BaseModel):
    egyptian: str = Field(min_length=1, max_length=100)
    formal: str = Field(min_length=1, max_length=100)
