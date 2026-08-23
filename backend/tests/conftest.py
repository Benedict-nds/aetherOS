import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.core.seed import seed_demo_user
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def seed_database():
    db = SessionLocal()
    try:
        seed_demo_user(db)
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
