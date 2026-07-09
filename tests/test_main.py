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


def test_maintenance_mode():
    from app.core.config import settings
    # Simulasikan MAINTENANCE_MODE = True
    settings.MAINTENANCE_MODE = True
    try:
        # Pengecekan route yang dikecualikan (harus tetap 200)
        res_root = client.get("/")
        assert res_root.status_code == 200

        res_health = client.get("/health")
        assert res_health.status_code == 200

        # Pengecekan route API biasa (harus diblokir dengan 503)
        res_auth = client.get("/api/v1/auth/me")
        assert res_auth.status_code == 503
        assert "pemeliharaan" in res_auth.json()["detail"]
        assert res_auth.headers.get("access-control-allow-origin") == "*"
    finally:
        # Kembalikan state awal
        settings.MAINTENANCE_MODE = False
