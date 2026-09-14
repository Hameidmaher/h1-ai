from pydantic import BaseModel, Field
from typing import Literal, Optional, Any
from datetime import date


class Product(BaseModel):
    item_code: str
    name: str
    category: str
    price: float
    stock_qty: int
    expiry_date: date
    description: str = ""


class AgentResponse(BaseModel):
    text: str
    action: Literal["answer", "redirect_to_pharmacist", "ask_clarification"] = "answer"
    products_referenced: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    needs_human: bool = False
    advisory: Optional[dict[str, Any]] = None


class User(BaseModel):
    id: str
    username: str
    role: Literal["customer", "pharmacist", "admin"]
    full_name: str = ""
    is_active: bool = True


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    full_name: str = ""


class RefreshRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    data: AgentResponse
    user_type: str
    session_id: str
    route_method: str = "keyword"
    handler: str = "agent"


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeAdviseRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
