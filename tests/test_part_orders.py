"""
Test untuk endpoint part orders (create & update) dengan berbagai format payload input.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_token() -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return res.json()["access_token"]


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


def test_create_order_with_list_input():
    headers = _auth_headers()
    # Create task first
    task_res = client.post(
        "/api/v1/line-stop",
        json={"noreg": "LS-TEST-PART", "part_no": "47781.2-0K090"},
        headers=headers,
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["data"]["id"]

    # Send order as List payload [ { part_cd: ... } ]
    order_payload = [
        {
            "part_cd": "123456789AWD",
            "part_name": "Shield Shock 20mm",
            "location": "WH01-R04-4A",
            "qty": 1
        }
    ]
    res = client.post(f"/api/v1/line-stop/{task_id}/orders", json=order_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["details"]) == 1
    assert data["details"][0]["part_cd"] == "123456789AWD"


def test_create_order_with_dict_input():
    headers = _auth_headers()
    task_res = client.post(
        "/api/v1/line-stop",
        json={"noreg": "LS-TEST-PART-2", "part_no": "47781.2-0K090"},
        headers=headers,
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["data"]["id"]

    # Send order as Dict payload { details: [ { part_cd: ... } ] }
    order_payload = {
        "details": [
            {
                "part_cd": "987654321AWD",
                "part_name": "Pin Guide 10mm",
                "location": "WH01-R02-1B",
                "qty": 2
            }
        ]
    }
    res = client.post(f"/api/v1/line-stop/{task_id}/orders", json=order_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["details"]) == 1
    assert data["details"][0]["part_cd"] == "987654321AWD"


def test_update_order_with_list_input():
    headers = _auth_headers()
    task_res = client.post(
        "/api/v1/line-stop",
        json={"noreg": "LS-TEST-PART-3", "part_no": "47781.2-0K090"},
        headers=headers,
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["data"]["id"]

    # 1. Create order
    create_payload = [
        {
            "part_cd": "123456789AWC",
            "part_name": "Shield Shock 7mm",
            "location": "WH01-R04-4A",
            "qty": 1
        }
    ]
    create_res = client.post(f"/api/v1/line-stop/{task_id}/orders", json=create_payload, headers=headers)
    assert create_res.status_code == 200
    order_id = create_res.json()["id"]

    # 2. PUT Update order with List payload
    update_payload = [
        {
            "part_cd": "123456789AWC",
            "part_name": "Shield Shock 7mm",
            "location": "WH01-R04-4A",
            "qty": 1
        },
        {
            "part_cd": "123456789AWB",
            "part_name": "Shield Shock 15mm",
            "location": "WH01-R04-4A",
            "qty": 1
        }
    ]
    update_res = client.put(f"/api/v1/line-stop/orders/{order_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert len(data["details"]) == 2
    assert data["details"][0]["part_cd"] == "123456789AWC"
    assert data["details"][1]["part_cd"] == "123456789AWB"

