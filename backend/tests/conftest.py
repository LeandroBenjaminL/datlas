"""Test fixtures: sample CSV data and database session override.

Provides a test database (SQLite in-memory) so tests don't require
a running PostgreSQL instance.
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base, get_db

FIXTURE_DIR = Path(__file__).parent / "data"


@pytest.fixture
def test_csv() -> Path:
    """Path to the sample test.csv fixture."""
    return FIXTURE_DIR / "test.csv"


@pytest.fixture
def test_csv_path(test_csv) -> str:
    """String path to the sample test.csv fixture."""
    return str(test_csv)


# ── Database fixtures ───────────────────────────────────────


@pytest.fixture(scope="session")
def test_engine():
    """SQLite in-memory engine shared across the test session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_db(test_engine):
    """Per-test database session with transaction rollback.

    Creates a new transaction per test and rolls it back on teardown,
    so tests are isolated without recreating the schema.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def override_get_db(app_with_db, test_db):
    """Override the FastAPI get_db dependency globally for all tests.

    Every test endpoint gets the test_db session automatically.
    """
    app_with_db.dependency_overrides[get_db] = lambda: test_db
    yield
    app_with_db.dependency_overrides.clear()


@pytest.fixture(scope="session")
def app_with_db():
    """FastAPI app instance (session-scoped, shared by all tests)."""
    from app.main import app

    return app
