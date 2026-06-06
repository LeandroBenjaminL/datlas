"""
Database engine and session configuration.

Provides SQLAlchemy engine, session factory, Base, and a FastAPI dependency
for per-request database sessions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


# ── Engine (sync — pandas-based services are sync anyway) ──
engine = create_engine(
    settings.database_url_sync,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # verify connections before use (Render connection drops)
    pool_size=5,  # Render free tier limit
    max_overflow=0,  # no extra connections beyond pool
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:
    """FastAPI dependency: yields a database session and closes it after request.

    Usage:
        @router.get("/something")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist (for dev convenience).

    In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
