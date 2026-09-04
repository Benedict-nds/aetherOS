import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.seed import seed_demo_user
from app.main import app
from app.models.audit_log import AuditLog
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def seed_database():
    """Reset test-created rows then seed the demo user.

    The suite runs against a persistent local database, so fixtures created by
    a previous run would otherwise collide on unique email/username columns.
    """
    db = SessionLocal()
    try:
        db.execute(delete(AuditLog))
        db.execute(delete(User).where(User.email != settings.demo_email))
        db.commit()
        seed_demo_user(db)
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
