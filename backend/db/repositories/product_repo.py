"""Product repository."""
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models.product import Product


class ProductRepository:
    """CRUD for products."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, item_code: str) -> Optional[Product]:
        stmt = select(Product).where(Product.item_code == str(item_code))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
    ) -> List[Product]:
        stmt = select(Product).offset(skip).limit(limit)
        if category:
            stmt = stmt.where(Product.category == category)
        return list(self.db.execute(stmt).scalars().all())

    def search(self, query: str, limit: int = 10) -> List[Product]:
        stmt = select(Product).where(
            Product.name.ilike(f"%{query}%")
        ).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, **kwargs) -> Product:
        product = Product(**kwargs)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def count(self) -> int:
        stmt = select(func.count(Product.id))
        return self.db.execute(stmt).scalar() or 0

    def seed_from_csv(self, csv_path: str) -> int:
        """Load products from CSV."""
        import csv
        count = 0
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing = self.get_by_code(row["ItemCode"])
                if existing:
                    continue
                self.db.add(Product(
                    item_code=str(row["ItemCode"]),
                    name=row["ItemName"],
                    category=row["Category"],
                    price=float(row["Price"]),
                    stock_qty=int(row["StockQty"]),
                    expiry_date=row["ExpiryDate"],
                    description=row.get("Description", ""),
                ))
                count += 1
        self.db.commit()
        return count
