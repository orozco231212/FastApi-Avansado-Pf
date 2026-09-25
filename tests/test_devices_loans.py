"""Pruebas funcionales de dispositivos, préstamos y consultas con joins."""

from fastapi.testclient import TestClient


def datos_de_usuario(email: str = "aprendiz@example.com") -> dict[str, object]:
    return {
        "name": "Ana Torres",
        "email": email,
        "role": "user",
        "is_active": True,
        "password": "UserPass123",
    }


def datos_de_dispositivo(serial: str = "LEN-001") -> dict[str, str]:
    return {
        "name": "ThinkPad T14",
        "serial_number": serial,
        "device_type": "laptop",
        "brand": "Lenovo",
    }


def test_ciclo_del_prestamo_y_filtros_con_joins(client: TestClient) -> None:
    usuario = client.post("/users", json=datos_de_usuario()).json()
    dispositivo = client.post("/devices", json=datos_de_dispositivo()).json()
    prestamo = client.post("/loans", json={"user_id": usuario["id"], "device_id": dispositivo["id"]})

    assert prestamo.status_code == 201
    assert client.get("/devices?is_available=false").json()[0]["id"] == dispositivo["id"]
    assert client.post("/loans", json={"user_id": usuario["id"], "device_id": dispositivo["id"]}).status_code == 409
    assert client.get("/loans?status=active&device_type=laptop").json()[0]["user"]["email"] == usuario["email"]
    assert client.get(f"/users/{usuario['id']}/loans").status_code == 200
    assert client.get(f"/devices/{dispositivo['id']}/loans").status_code == 200

    identificador = prestamo.json()["id"]
    assert client.patch(f"/loans/{identificador}/return").status_code == 200
    assert client.get(f"/devices/{dispositivo['id']}").json()["is_available"] is True
    assert client.patch(f"/loans/{identificador}/return").status_code == 409
