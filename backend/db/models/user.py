"""User ORM model."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class User(Base):
    """User model — customer, pharmacist, admin."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=True,
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=True,
    )
    full_name: Mapped[str] = mapped_column(String(100), default="")
    role: Mapped[str] = mapped_column(
        String(20), default="customer", index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    pharmacy_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "pharmacy_id": self.pharmacy_id,
        }
