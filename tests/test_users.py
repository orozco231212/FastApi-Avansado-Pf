from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.main import app

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
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def user_payload(email: str = "ana@example.com") -> dict[str, object]:
    return {
        "name": "Ana Torres",
        "email": email,
        "role": "admin",
        "is_active": True,
    }


def test_user_crud_and_filters(client: TestClient) -> None:
    response = client.post("/users", json=user_payload())
    assert response.status_code == 201
    user_id = response.json()["id"]

    assert client.get("/users?role=admin").status_code == 200
    assert len(client.get("/users?is_active=true").json()) == 1
    assert client.get(f"/users/{user_id}").json()["email"] == "ana@example.com"

    response = client.put(
        f"/users/{user_id}",
        json={**user_payload("ana.updated@example.com"), "name": "Ana Updated"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Ana Updated"

    response = client.patch(f"/users/{user_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    assert client.delete(f"/users/{user_id}").status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404


def test_duplicate_email_and_validation(client: TestClient) -> None:
    assert client.post("/users", json=user_payload()).status_code == 201
    duplicate = client.post("/users", json=user_payload("ana@example.com"))
    assert duplicate.status_code == 400

    invalid = client.post(
        "/users",
        json={"name": "Al", "email": "not-an-email", "role": "owner"},
    )
    assert invalid.status_code == 422


def test_missing_user_errors(client: TestClient) -> None:
    assert client.get("/users/999").status_code == 404
    assert client.put("/users/999", json=user_payload()).status_code == 404
    assert client.patch("/users/999", json={"name": "Nuevo Nombre"}).status_code == 404
    assert client.delete("/users/999").status_code == 404