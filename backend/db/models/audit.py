"""Audit Log ORM model."""
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class AuditLog(Base):
    """Audit log for all actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    username: Mapped[str] = mapped_column(String(50))

    action: Mapped[str] = mapped_column(String(50), index=True)
    # CREATE, UPDATE, DELETE, LOGIN, LOGOUT

    entity: Mapped[str] = mapped_column(String(50), index=True)
    # product, drug, user, prescription

    entity_id: Mapped[str] = mapped_column(String(100), index=True, default="")
    details: Mapped[str] = mapped_column(Text, default="")  # JSON

    ip_address: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(String(300), default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
