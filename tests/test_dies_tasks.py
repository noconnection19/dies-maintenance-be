"""
Test untuk router Dies Line Stop (dapat digunakan sebagai template untuk repair & preventive).
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ── Helpers ──────────────────────────────────────────────────────────
def _get_token() -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return res.json()["access_token"]


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


# ── Tests ────────────────────────────────────────────────────────────
def test_list_line_stop_unauthenticated():
    response = client.get("/api/v1/line-stop/")
    assert response.status_code == 401


def test_create_and_list_line_stop():
    headers = _auth_headers()

    create_res = client.post(
        "/api/v1/line-stop/",
        json={"noreg": "LS-001", "part_no": "P-100", "description": "Test task"},
        headers=headers,
    )
    assert create_res.status_code == 201

    list_res = client.get("/api/v1/line-stop/", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["pagination"]["total"] >= 1
