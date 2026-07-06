"""
Test untuk endpoint health dan root.

Menjalankan test:
    pytest tests/ -v
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "app" in data
    assert "version" in data


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200


def test_login_wrong_credentials():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "salah", "password": "salah"},
    )
    assert response.status_code == 401


def test_protected_without_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
