import os
"""Seed database from CSV."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import SessionLocal
from db.repositories import (
    UserRepository,
    ProductRepository,
)
from auth.jwt_handler import hash_password


def main():
    print("🌱 Seeding database...")

    db = SessionLocal()
    try:
        # Users
        user_repo = UserRepository(db)
        if user_repo.count() == 0:
            print("  👤 Creating users...")
            user_repo.create(
                username="admin",
                hashed_password=hash_password(os.getenv("ADMIN_SEED_PASSWORD", "change-me-in-production")),
                role="admin",
                full_name="مدير النظام",
                email="admin@h1-ai.com",
            )
            user_repo.create(
                username="customer1",
                hashed_password=hash_password("customer123"),
                role="customer",
                full_name="عميل تجريبي",
            )
            user_repo.create(
                username="pharmacist1",
                hashed_password=hash_password("pharma123"),
                role="pharmacist",
                full_name="صيدلي تجريبي",
            )
            print(f"     ✅ {user_repo.count()} users")

        # Products from CSV
        product_repo = ProductRepository(db)
        if product_repo.count() == 0:
            print("  📦 Loading products...")
            csv_path = Path(__file__).parent.parent.parent / "data" / "products.csv"
            if csv_path.exists():
                count = product_repo.seed_from_csv(str(csv_path))
                print(f"     ✅ {count} products loaded")
            else:
                print(f"     ⚠️  CSV not found: {csv_path}")
        else:
            print(f"  📦 Already has {product_repo.count()} products")

        print()
        print("✅ Database seeding complete!")
        print(f"   Users:    {user_repo.count()}")
        print(f"   Products: {product_repo.count()}")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
