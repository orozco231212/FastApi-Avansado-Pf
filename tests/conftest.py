from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.auth.security import create_access_token, get_password_hash
from app.main import app
from app.models.user_model import User
from app.middlewares.rate_limiter import limiter

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    limiter._storage.reset()
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    admin = User(
        name="Admin de Pruebas",
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    token = create_access_token({"sub": str(admin.id)})
    db.close()
    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)