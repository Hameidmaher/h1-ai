"""Auth models — Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Literal, Optional


Role = Literal["customer", "pharmacist", "admin", "super_admin"]


class User(BaseModel):
    """Public user (no password)."""
    id: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1, max_length=50)
    role: Role
    full_name: str = ""
    is_active: bool = True
    pharmacy_id: Optional[str] = None  # ← NULL = Super Admin


class UserInDB(User):
    """Internal user with hashed password."""
    hashed_password: str


class TokenPayload(BaseModel):
    """JWT payload structure."""
    sub: str          # user_id
    username: str
    role: str
    pharmacy_id: Optional[str] = None  # ← جديد
    exp: int
    iat: int | None = None
    type: Literal["access", "refresh"] = "access"
