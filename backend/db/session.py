"""Database session — supports SQLite and PostgreSQL."""
from __future__ import annotations
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os

# ─── IMPORTANT: Load .env BEFORE accessing os.environ ───
try:
    from dotenv import load_dotenv
    # Load from backend/.env
    _env_file = Path(__file__).parent.parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=True)
except ImportError:
    pass


def _get_database_url() -> str:
    """Get database URL from env or fallback to SQLite."""
    url = os.getenv("DATABASE_URL")
    
    if url and url.strip():
        # Print info (but hide password)
        display_url = url
        if "@" in url:
            parts = url.split("@")
            display_url = parts[0].split("://")[0] + "://***@" + parts[1]
        print(f"✅ [DB] Using PostgreSQL: {display_url}")
        return url
    
    # Fallback to SQLite
    sqlite_path = Path(__file__).parent.parent / "h1ai.db"
    print(f"⚠️  [DB] Using SQLite: {sqlite_path}")
    return f"sqlite:///{sqlite_path}"


def _create_engine():
    """Create engine with appropriate settings."""
    url = _get_database_url()
    
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
            echo=False,
        )
    else:
        return create_engine(
            url,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )


engine = _create_engine()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
