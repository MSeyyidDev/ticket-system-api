"""SQLAlchemy 2.0 engine, session, and declarative base."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _build_engine(database_url: str):
    connect_args: dict = {}
    if database_url.startswith("sqlite"):
        # SQLite needs this so the same connection can be used across threads
        # (FastAPI dependency injection runs handlers in a thread pool).
        connect_args["check_same_thread"] = False
    return create_engine(database_url, future=True, connect_args=connect_args)


_settings = get_settings()
engine = _build_engine(_settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a per-request SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Idempotent — safe to call on every startup."""
    # Importing models here ensures they are registered on Base.metadata
    # before create_all runs.
    from app import models  # noqa: F401  (side-effect import)

    Base.metadata.create_all(bind=engine)
