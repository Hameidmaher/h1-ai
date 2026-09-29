"""User repository — data access layer."""
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.user import User


class UserRepository:
    """CRUD for users."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_phone(self, phone: str) -> Optional[User]:
        stmt = select(User).where(User.phone == phone)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        pharmacy_id: Optional[str] = None,
    ) -> List[User]:
        stmt = select(User).offset(skip).limit(limit)
        if role:
            stmt = stmt.where(User.role == role)
        if pharmacy_id is not None:
            stmt = stmt.where(User.pharmacy_id == pharmacy_id)
        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        username: str,
        hashed_password: str,
        role: str = "customer",
        full_name: str = "",
        email: Optional[str] = None,
        phone: Optional[str] = None,
        pharmacy_id: Optional[str] = None,
    ) -> User:
        user = User(
            id=str(uuid4()),
            username=username,
            hashed_password=hashed_password,
            role=role,
            full_name=full_name,
            email=email,
            phone=phone,
            pharmacy_id=pharmacy_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: str, **kwargs) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        for k, v in kwargs.items():
            if hasattr(user, k) and v is not None:
                setattr(user, k, v)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def count(self, role: Optional[str] = None) -> int:
        from sqlalchemy import func
        stmt = select(func.count(User.id))
        if role:
            stmt = stmt.where(User.role == role)
        return self.db.execute(stmt).scalar() or 0
