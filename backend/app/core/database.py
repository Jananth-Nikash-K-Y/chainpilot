"""SQLAlchemy engine/session setup.

Provides the declarative base, engine, session factory, and a FastAPI
dependency (``get_db``) that yields a session per request.

The default database is SQLite (a single ``chainpilot.db`` file, no server
to install or run). Point ``DATABASE_URL`` at PostgreSQL later and nothing
above this module has to change.
"""
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

# SQLite needs check_same_thread=False so the connection can be reused across
# FastAPI's threadpool workers. pool_pre_ping only makes sense for a network DB.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,
)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _connection_record) -> None:
        """SQLite ignores FOREIGN KEY constraints unless asked not to."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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
