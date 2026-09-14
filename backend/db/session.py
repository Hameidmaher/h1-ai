"""Database session management."""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config_loader import prod_config

# ═══════════════════════════════════════════════════════════
# Database URL
# ═══════════════════════════════════════════════════════════
db_type = os.getenv("DATABASE_TYPE", "sqlite")

if db_type == "postgres":
    pg = prod_config.get("database.postgres", {})
    user = pg.get("user", "postgres")
    password = pg.get("password", "")
    host = pg.get("host", "localhost")
    port = pg.get("port", 5432)
    database = pg.get("database", "h1ai")
    DATABASE_URL = (
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )
else:
    # SQLite fallback
    DATABASE_URL = "sqlite:///./h1ai.db"


# ═══════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ═══════════════════════════════════════════════════════════
# Dependencies
# ═══════════════════════════════════════════════════════════
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for scripts."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
