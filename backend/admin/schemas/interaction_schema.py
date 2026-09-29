from pydantic import BaseModel, Field
from typing import Literal


class InteractionCreate(BaseModel):
    drug1: str = Field(min_length=2)
    drug2: str = Field(min_length=2)
    severity: Literal["minor", "moderate", "major"] = "moderate"
    effect: str = Field(min_length=2)
    action: str = Field(min_length=2)


class InteractionUpdate(BaseModel):
    severity: Literal["minor", "moderate", "major"] | None = None
    effect: str | None = None
    action: str | None = None
