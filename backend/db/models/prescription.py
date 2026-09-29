"""Prescription ORM model."""
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Prescription(Base):
    """Prescription uploaded by customer."""

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    image_path: Mapped[str] = mapped_column(String(500))

    # OCR Results
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    extracted_drugs: Mapped[str] = mapped_column(Text, default="")  # JSON

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True,
    )  # pending, approved, rejected, dispensed

    # Pharmacist Review
    reviewed_by: Mapped[str] = mapped_column(String(36), nullable=True)
    pharmacist_notes: Mapped[str] = mapped_column(Text, default="")

    # Safety
    interactions_found: Mapped[str] = mapped_column(Text, default="")  # JSON
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_path": self.image_path,
            "extracted_text": self.extracted_text,
            "extracted_drugs": self.extracted_drugs,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "pharmacist_notes": self.pharmacist_notes,
            "interactions_found": self.interactions_found,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
