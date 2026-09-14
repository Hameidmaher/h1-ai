"""User-related Pydantic schemas."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: str = ""
    role: str
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)


class UserCreateAdmin(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    role: str = Field(pattern="^(customer|pharmacist|admin)$")
    full_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None


class UserList(BaseModel):
    items: list[UserResponse]
    total: int
    page: int = 1
    page_size: int = 20
