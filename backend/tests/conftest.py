import os
import sys
import pytest
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.db.init_db import init_db

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Ensure database is seeded fresh before every test."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield

@pytest.fixture
def db_session():
    """Yield a database session and rollback or close."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
