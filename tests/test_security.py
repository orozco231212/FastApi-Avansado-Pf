"""Pruebas funcionales de la capa de seguridad: registro, login, JWT, roles, CORS y límites."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.auth_schema import UserRegister


def datos_de_registro(email: str = "aprendiz@example.com") -> dict[str, str]:
    return {"name": "Ana Torres", "email": email, "password": "ClaveSegura123"}


def iniciar_sesion(client: TestClient, email: str, password: str = "ClaveSegura123") -> str:
    respuesta = client.post("/auth/login", data={"username": email, "password": password})
    assert respuesta.status_code == 200
    return respuesta.json()["access_token"]


def test_registro_login_y_usuario_actual(client: TestClient) -> None:
    registrado = client.post("/auth/register", json=datos_de_registro())
    assert registrado.status_code == 201
    assert registrado.json()["role"] == "user"
    assert "hashed_password" not in registrado.json()

    token = iniciar_sesion(client, "aprendiz@example.com")
    usuario_actual = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert usuario_actual.status_code == 200
    assert usuario_actual.json()["email"] == "aprendiz@example.com"
    assert "hashed_password" not in usuario_actual.json()


def test_validacion_de_contrasena_y_email_duplicado(client: TestClient) -> None:
    contrasena_debil = client.post("/auth/register", json={**datos_de_registro(), "password": "debil"})
    assert contrasena_debil.status_code == 422

    escalamiento_de_rol = client.post("/auth/register", json={**datos_de_registro(), "role": "admin"})
    assert escalamiento_de_rol.status_code == 422

    assert client.post("/auth/register", json=datos_de_registro()).status_code == 201
    duplicado = client.post("/auth/register", json=datos_de_registro())
    assert duplicado.status_code == 400

    login_invalido = client.post(
        "/auth/login",
        data={"username": "aprendiz@example.com", "password": "WrongPass123"},
    )
    assert login_invalido.status_code == 401


def test_autenticacion_y_proteccion_por_roles(client: TestClient) -> None:
    assert client.get("/users", headers={"Authorization": ""}).status_code == 401
    assert client.get("/users", headers={"Authorization": "Bearer invalido"}).status_code == 401

    client.post("/auth/register", json=datos_de_registro())
    token = iniciar_sesion(client, "aprendiz@example.com")
    cabeceras = {"Authorization": f"Bearer {token}"}
    assert client.get("/users", headers=cabeceras).status_code == 200
    assert client.post(
        "/devices",
        headers=cabeceras,
        json={"name": "Portátil", "serial_number": "LT-01", "device_type": "laptop"},
    ).status_code == 403

    dispositivo = client.post(
        "/devices",
        json={"name": "Portátil", "serial_number": "LT-02", "device_type": "laptop"},
    ).json()
    denegado = client.delete(f"/devices/{dispositivo['id']}", headers=cabeceras)
    assert denegado.status_code == 403


def test_cabeceras_del_middleware_y_cors(client: TestClient) -> None:
    respuesta = client.get("/", headers={"X-Request-ID": "prueba-123"})
    assert respuesta.headers["X-App-Name"] == "device_systems"
    assert respuesta.headers["X-Request-ID"] == "prueba-123"
    assert float(respuesta.headers["X-Process-Time"]) >= 0

    preflight = client.options(
        "/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_limite_de_registro(client: TestClient) -> None:
    respuestas = [
        client.post("/auth/register", json=datos_de_registro(f"usuario{indice}@example.com"))
        for indice in range(4)
    ]
    assert [respuesta.status_code for respuesta in respuestas] == [201, 201, 201, 429]
    excedida = respuestas[-1]
    assert "x-ratelimit-limit" in {nombre.lower() for nombre in excedida.headers}
    assert "retry-after" in {nombre.lower() for nombre in excedida.headers}
    assert "Demasiadas solicitudes" in excedida.json()["detail"]


def test_limite_de_login(client: TestClient) -> None:
    client.post("/auth/register", json=datos_de_registro())
    estados = [
        client.post(
            "/auth/login",
            data={"username": "aprendiz@example.com", "password": "WrongPass123"},
        ).status_code
        for _ in range(6)
    ]
    assert estados == [401, 401, 401, 401, 401, 429]


def test_variantes_de_politica_de_contrasenas() -> None:
    contrasenas_invalidas = [
        "Short1",  # menos de 8 caracteres
        "sinmayuscula1",  # sin mayúscula
        "SINMINUSCULA1",  # sin minúscula
        "SinNumeroAqui",  # sin número
        "Con Espacio1",  # contiene espacios
        "AnaSegura123",  # contiene la parte local del correo
    ]
    for contrasena in contrasenas_invalidas:
        with pytest.raises(ValidationError):
            UserRegister(name="Ana Torres", email="ana@example.com", password=contrasena)


def test_rutas_protegidas_exigen_token(client: TestClient) -> None:
    anonimo = {"Authorization": ""}
    assert client.get("/users", headers=anonimo).status_code == 401
    assert client.get("/users/1", headers=anonimo).status_code == 401
    assert client.get("/devices", headers=anonimo).status_code == 401
    assert client.post("/loans", headers=anonimo, json={"user_id": 1, "device_id": 1}).status_code == 401
    assert client.get("/loans/details", headers=anonimo).status_code == 401
    assert client.get("/auth/me", headers=anonimo).status_code == 401


def test_detalle_de_prestamos_solo_para_staff(client: TestClient) -> None:
    client.post("/auth/register", json=datos_de_registro())
    token = iniciar_sesion(client, "aprendiz@example.com")
    cabeceras = {"Authorization": f"Bearer {token}"}
    assert client.get("/loans", headers=cabeceras).status_code == 403
    assert client.get("/loans/details", headers=cabeceras).status_code == 403


def test_el_hash_nunca_se_expone(client: TestClient) -> None:
    creado = client.post(
        "/users",
        json={
            "name": "Soporte SENA",
            "email": "soporte@example.com",
            "role": "support",
            "is_active": True,
            "password": "SoportePass123",
        },
    )
    assert creado.status_code == 201
    assert "hashed_password" not in creado.json()
    listado = client.get("/users")
    assert all("hashed_password" not in usuario for usuario in listado.json())


def test_cabeceras_de_seguridad_del_middleware(client: TestClient) -> None:
    respuesta = client.get("/")
    assert respuesta.headers["X-Content-Type-Options"] == "nosniff"
    assert respuesta.headers["X-Frame-Options"] == "DENY"
    assert respuesta.headers["Referrer-Policy"] == "no-referrer"


def test_endpoint_de_politica_de_seguridad(client: TestClient) -> None:
    respuesta = client.get("/security/policy", headers={"Authorization": ""})
    assert respuesta.status_code == 200
    politica = respuesta.json()
    assert politica["app_name"] == "device_systems"
    assert politica["rate_limits"]["POST /auth/login"] == "5/minute"
    assert politica["password_policy"]["hash_algorithm"] == "bcrypt_sha256"
    assert politica["jwt_policy"]["algorithm"] == "HS256"
    assert "http://localhost:5173" in politica["cors_allowed_origins"]


def test_mensajes_de_error_en_espanol(client: TestClient) -> None:
    sin_token = client.get("/users", headers={"Authorization": ""})
    assert sin_token.status_code == 401
    assert "No autenticado" in sin_token.json()["detail"]

    token_invalido = client.get("/users", headers={"Authorization": "Bearer invalido"})
    assert token_invalido.status_code == 401
    assert "Token inválido" in token_invalido.json()["detail"]

    contrasena_debil = client.post("/auth/register", json={**datos_de_registro(), "password": "debil"})
    assert contrasena_debil.status_code == 422
    cuerpo = contrasena_debil.json()
    assert cuerpo["detail"] == "Los datos enviados no son válidos"
    errores = {error["campo"]: error["mensaje"] for error in cuerpo["errores"]}
    assert "8 caracteres" in errores["password"]

    campo_extra = client.post("/auth/register", json={**datos_de_registro(), "role": "admin"})
    mensajes = {error["campo"]: error["mensaje"] for error in campo_extra.json()["errores"]}
    assert mensajes["role"] == "El campo no está permitido"

    inexistente = client.get("/ruta/que/no/existe", headers={"Authorization": ""})
    assert inexistente.status_code == 404
    assert inexistente.json()["detail"] == "Recurso no encontrado"

