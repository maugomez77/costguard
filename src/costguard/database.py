"""PostgreSQL adapter for Cost Guard.

Uses a single JSONB blob keyed by 'main' — mirrors the JSON file layout so
store.py can swap file I/O for DB I/O without touching any call sites.
Falls back to JSON file when DATABASE_URL is unset (local dev / CLI).
"""

from __future__ import annotations

import os

from sqlalchemy import Column, DateTime, String, create_engine, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

for _prefix in ("postgresql+asyncpg://", "postgresql+psycopg://", "postgresql+psycopg2://"):
    if DATABASE_URL.startswith(_prefix):
        DATABASE_URL = DATABASE_URL.replace(_prefix, "postgresql://", 1)
        break

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False) if engine else None

Base = declarative_base()


class KVStore(Base):
    __tablename__ = "costguard_store"

    key = Column(String, primary_key=True)
    value = Column(JSONB, nullable=False, default=dict)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def is_db_enabled() -> bool:
    return engine is not None


def init_db() -> None:
    if engine is not None:
        Base.metadata.create_all(engine)
