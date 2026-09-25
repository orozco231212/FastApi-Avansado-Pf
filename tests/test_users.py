"""Pruebas funcionales del recurso de usuarios."""

from fastapi.testclient import TestClient


def datos_de_usuario(email: str = "ana@example.com") -> dict[str, object]:
    return {
        "name": "Ana Torres",
        "email": email,
        "role": "admin",
        "is_active": True,
        "password": "UserPass123",
    }


def test_crud_y_filtros_de_usuarios(client: TestClient) -> None:
    respuesta = client.post("/users", json=datos_de_usuario())
    assert respuesta.status_code == 201, respuesta.text
    identificador = respuesta.json()["id"]

    assert client.get("/users?role=admin").status_code == 200
    assert len(client.get("/users?is_active=true").json()) == 2
    assert client.get(f"/users/{identificador}").json()["email"] == "ana@example.com"

    respuesta = client.put(
        f"/users/{identificador}",
        json={**datos_de_usuario("ana.updated@example.com"), "name": "Ana Actualizada"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["name"] == "Ana Actualizada"

    respuesta = client.patch(f"/users/{identificador}", json={"is_active": False})
    assert respuesta.status_code == 200
    assert respuesta.json()["is_active"] is False

    assert client.delete(f"/users/{identificador}").status_code == 204
    assert client.get(f"/users/{identificador}").status_code == 404


def test_email_duplicado_y_validaciones(client: TestClient) -> None:
    assert client.post("/users", json=datos_de_usuario()).status_code == 201
    duplicado = client.post("/users", json=datos_de_usuario("ana@example.com"))
    assert duplicado.status_code == 400

    invalido = client.post(
        "/users",
        json={"name": "Al", "email": "no-es-un-correo", "role": "propietario"},
    )
    assert invalido.status_code == 422


def test_errores_de_usuario_inexistente(client: TestClient) -> None:
    assert client.get("/users/999").status_code == 404
    assert client.put("/users/999", json=datos_de_usuario()).status_code == 404
    assert client.patch("/users/999", json={"name": "Nombre Nuevo"}).status_code == 404
    assert client.delete("/users/999").status_code == 404
