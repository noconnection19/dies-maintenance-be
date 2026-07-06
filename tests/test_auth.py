"""
Test untuk router Auth.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_success():
    # Seed admin harus sudah berjalan (dipanggil via lifespan di startup)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "Admin"


def test_get_me():
    # Login dulu
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
