import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.database import Base
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables before tests run, drop after.
    Uses Base.metadata.create_all() — faster than running Alembic migrations.
    Works against both local and CI Postgres instances.
    """
    SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")
    engine = create_engine(SYNC_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)