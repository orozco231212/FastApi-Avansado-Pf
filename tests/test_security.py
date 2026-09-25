import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.auth_schema import UserRegister


def registration_payload(email: str = "aprendiz@example.com") -> dict[str, str]:
    return {"name": "Ana Torres", "email": email, "password": "ClaveSegura123"}


def login(client: TestClient, email: str, password: str = "ClaveSegura123") -> str:
    response = client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_login_and_current_user(client: TestClient) -> None:
    registered = client.post("/auth/register", json=registration_payload())
    assert registered.status_code == 201
    assert registered.json()["role"] == "user"
    assert "hashed_password" not in registered.json()

    token = login(client, "aprendiz@example.com")
    current_user = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert current_user.status_code == 200
    assert current_user.json()["email"] == "aprendiz@example.com"
    assert "hashed_password" not in current_user.json()


def test_password_validation_and_duplicate_email(client: TestClient) -> None:
    weak_password = client.post(
        "/auth/register",
        json={**registration_payload(), "password": "weak"},
    )
    assert weak_password.status_code == 422

    role_escalation = client.post(
        "/auth/register",
        json={**registration_payload(), "role": "admin"},
    )
    assert role_escalation.status_code == 422

    assert client.post("/auth/register", json=registration_payload()).status_code == 201
    duplicate = client.post("/auth/register", json=registration_payload())
    assert duplicate.status_code == 400

    invalid_login = client.post(
        "/auth/login",
        data={"username": "aprendiz@example.com", "password": "WrongPass123"},
    )
    assert invalid_login.status_code == 401


def test_authentication_and_role_protection(client: TestClient) -> None:
    assert client.get("/users", headers={"Authorization": ""}).status_code == 401
    assert client.get("/users", headers={"Authorization": "Bearer invalid"}).status_code == 401

    client.post("/auth/register", json=registration_payload())
    token = login(client, "aprendiz@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/users", headers=headers).status_code == 200
    assert client.post(
        "/devices",
        headers=headers,
        json={"name": "Laptop", "serial_number": "LT-01", "device_type": "laptop"},
    ).status_code == 403

    device = client.post(
        "/devices",
        json={"name": "Laptop", "serial_number": "LT-02", "device_type": "laptop"},
    ).json()
    denied_delete = client.delete(f"/devices/{device['id']}", headers=headers)
    assert denied_delete.status_code == 403


def test_middleware_and_cors_headers(client: TestClient) -> None:
    response = client.get("/", headers={"X-Request-ID": "test-request-123"})
    assert response.headers["X-App-Name"] == "device_systems"
    assert response.headers["X-Request-ID"] == "test-request-123"
    assert float(response.headers["X-Process-Time"]) >= 0

    preflight = client.options(
        "/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_register_rate_limit(client: TestClient) -> None:
    results = [
        client.post("/auth/register", json=registration_payload(f"user{index}@example.com"))
        for index in range(4)
    ]
    assert [response.status_code for response in results] == [201, 201, 201, 429]
    assert "x-ratelimit-limit" in {name.lower() for name in results[-1].headers}
    assert "retry-after" in {name.lower() for name in results[-1].headers}


def test_login_rate_limit(client: TestClient) -> None:
    client.post("/auth/register", json=registration_payload())
    statuses = [
        client.post(
            "/auth/login",
            data={"username": "aprendiz@example.com", "password": "WrongPass123"},
        ).status_code
        for _ in range(6)
    ]
    assert statuses == [401, 401, 401, 401, 401, 429]


def test_password_policy_variants() -> None:
    invalid_passwords = [
        "Short1",  # menos de 8 caracteres
        "sinmayuscula1",  # sin mayúscula
        "SINMINUSCULA1",  # sin minúscula
        "SinNumeroAqui",  # sin número
        "Con Espacio1",  # contiene espacios
        "AnaSegura123",  # contiene la parte local del correo
    ]
    for password in invalid_passwords:
        with pytest.raises(ValidationError):
            UserRegister(name="Ana Torres", email="ana@example.com", password=password)


def test_protected_routes_require_token(client: TestClient) -> None:
    anonymous = {"Authorization": ""}
    assert client.get("/users", headers=anonymous).status_code == 401
    assert client.get("/users/1", headers=anonymous).status_code == 401
    assert client.get("/devices", headers=anonymous).status_code == 401
    assert client.post("/loans", headers=anonymous, json={"user_id": 1, "device_id": 1}).status_code == 401
    assert client.get("/loans/details", headers=anonymous).status_code == 401
    assert client.get("/auth/me", headers=anonymous).status_code == 401


def test_staff_only_loan_details(client: TestClient) -> None:
    client.post("/auth/register", json=registration_payload())
    token = login(client, "aprendiz@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/loans", headers=headers).status_code == 403
    assert client.get("/loans/details", headers=headers).status_code == 403


def test_hashed_password_never_exposed(client: TestClient) -> None:
    created = client.post(
        "/users",
        json={
            "name": "Soporte SENA",
            "email": "soporte@example.com",
            "role": "support",
            "is_active": True,
            "password": "SoportePass123",
        },
    )
    assert created.status_code == 201
    assert "hashed_password" not in created.json()
    listed = client.get("/users")
    assert all("hashed_password" not in user for user in listed.json())


def test_middleware_security_headers(client: TestClient) -> None:
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_security_policy_endpoint(client: TestClient) -> None:
    response = client.get("/security/policy", headers={"Authorization": ""})
    assert response.status_code == 200
    policy = response.json()
    assert policy["app_name"] == "device_systems"
    assert policy["rate_limits"]["POST /auth/login"] == "5/minute"
    assert policy["password_policy"]["hash_algorithm"] == "bcrypt_sha256"
    assert policy["jwt_policy"]["algorithm"] == "HS256"
    assert "http://localhost:5173" in policy["cors_allowed_origins"]
