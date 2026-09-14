from pydantic import BaseModel
from typing import Literal


class User(BaseModel):
    id: str
    username: str
    role: Literal["customer", "pharmacist", "admin"]
    full_name: str = ""
    is_active: bool = True


class UserInDB(User):
    hashed_password: str


class TokenPayload(BaseModel):
    sub: str
    username: str
    role: str
    exp: int
    type: Literal["access", "refresh"] = "access"
