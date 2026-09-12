from fastapi.testclient import TestClient


def user_payload(email: str = "aprendiz@example.com") -> dict[str, object]:
    return {"name": "Ana Torres", "email": email, "role": "user", "is_active": True}


def device_payload(serial_number: str = "LEN-001") -> dict[str, str]:
    return {
        "name": "ThinkPad T14",
        "serial_number": serial_number,
        "device_type": "laptop",
        "brand": "Lenovo",
    }


def test_loan_lifecycle_and_join_filters(client: TestClient) -> None:
    user = client.post("/users", json=user_payload()).json()
    device = client.post("/devices", json=device_payload()).json()
    loan = client.post("/loans", json={"user_id": user["id"], "device_id": device["id"]})

    assert loan.status_code == 201
    assert client.get("/devices?is_available=false").json()[0]["id"] == device["id"]
    assert client.post("/loans", json={"user_id": user["id"], "device_id": device["id"]}).status_code == 409
    assert client.get("/loans?status=active&device_type=laptop").json()[0]["user"]["email"] == user["email"]
    assert client.get(f"/users/{user['id']}/loans").status_code == 200
    assert client.get(f"/devices/{device['id']}/loans").status_code == 200

    loan_id = loan.json()["id"]
    assert client.patch(f"/loans/{loan_id}/return").status_code == 200
    assert client.get(f"/devices/{device['id']}").json()["is_available"] is True
    assert client.patch(f"/loans/{loan_id}/return").status_code == 409