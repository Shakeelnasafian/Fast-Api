from __future__ import annotations


def test_health_endpoints_expose_operational_status(client):
    live_response = client.get("/health/live")
    ready_response = client.get("/health/ready")

    assert live_response.status_code == 200
    assert ready_response.status_code == 200
    assert live_response.json() == {"status": "ok"}
    assert ready_response.json() == {"status": "ok"}
    assert "X-Request-ID" in live_response.headers


def test_auth_flow_issues_and_accepts_bearer_tokens(client):
    register_response = client.post(
        "/auth/register",
        json={"username": "FleetAdmin", "password": "StrongPass123"},
    )
    token_response = client.post(
        "/auth/token",
        data={"username": "FleetAdmin", "password": "StrongPass123"},
    )

    assert register_response.status_code == 201
    assert register_response.json()["username"] == "fleetadmin"

    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    assert token_response.json()["token_type"] == "bearer"

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "fleetadmin"


def test_car_crud_and_trip_validation(client):
    create_response = client.post(
        "/api/cars/",
        json={
            "size": "m",
            "doors": 5,
            "transmission": "manual",
            "fuel": "hybrid",
        },
    )
    assert create_response.status_code == 201
    car_id = create_response.json()["id"]

    trip_response = client.post(
        f"/api/cars/{car_id}/trips",
        json={"start": 10, "end": 20, "description": "Airport transfer"},
    )
    invalid_trip_response = client.post(
        f"/api/cars/{car_id}/trips",
        json={"start": 20, "end": 10, "description": "Broken booking"},
    )

    assert trip_response.status_code == 201
    assert invalid_trip_response.status_code == 422

    list_response = client.get("/api/cars/", params={"size": "m", "doors": 4})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert len(list_response.json()[0]["trips"]) == 1

    update_response = client.put(
        f"/api/cars/{car_id}",
        json={
            "size": "l",
            "doors": 5,
            "transmission": "auto",
            "fuel": "electric",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["size"] == "l"

    delete_response = client.delete(f"/api/cars/{car_id}")
    missing_response = client.get(f"/api/cars/{car_id}")

    assert delete_response.status_code == 204
    assert missing_response.status_code == 404
