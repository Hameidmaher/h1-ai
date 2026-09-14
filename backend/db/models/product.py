"""Product ORM model."""
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Product(Base):
    """Pharmacy product."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_code: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    expiry_date: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text, default="")

    def to_dict(self) -> dict:
        return {
            "item_code": self.item_code,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "stock_qty": self.stock_qty,
            "expiry_date": self.expiry_date,
            "description": self.description,
        }
