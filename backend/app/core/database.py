"""SQLAlchemy engine/session setup.

Provides the declarative base, engine, session factory, and a FastAPI
dependency (``get_db``) that yields a session per request.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all future ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency – yields a DB session, closes on teardown."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
