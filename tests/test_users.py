"""User CRUD tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_users_paginated(client: TestClient, admin_headers: dict[str, str]) -> None:
    resp = client.get("/users?page=1&page_size=10", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total"] >= 3
    assert any(item["email"] == "admin@example.com" for item in body["items"])


def test_create_user_as_admin(client: TestClient, admin_headers: dict[str, str]) -> None:
    resp = client.post(
        "/users",
        headers=admin_headers,
        json={
            "email": "newhire@example.com",
            "full_name": "New Hire",
            "department": "Engineering",
            "role": "agent",
            "password": "supersecret",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newhire@example.com"
    assert body["role"] == "agent"


def test_create_user_requires_admin(client: TestClient, user_headers: dict[str, str]) -> None:
    resp = client.post(
        "/users",
        headers=user_headers,
        json={
            "email": "x@example.com",
            "full_name": "Nope",
            "role": "requester",
            "password": "supersecret",
        },
    )
    assert resp.status_code == 403


def test_create_user_duplicate_email(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    payload = {
        "email": "dup@example.com",
        "full_name": "First",
        "role": "requester",
        "password": "supersecret",
    }
    first = client.post("/users", headers=admin_headers, json=payload)
    assert first.status_code == 201
    second = client.post("/users", headers=admin_headers, json=payload)
    assert second.status_code == 409


def test_get_user_not_found(client: TestClient, admin_headers: dict[str, str]) -> None:
    resp = client.get("/users/999999", headers=admin_headers)
    assert resp.status_code == 404


def test_update_user(client: TestClient, admin_headers: dict[str, str]) -> None:
    create = client.post(
        "/users",
        headers=admin_headers,
        json={
            "email": "promoteme@example.com",
            "full_name": "Promote Me",
            "role": "requester",
            "password": "supersecret",
        },
    )
    user_id = create.json()["id"]
    resp = client.put(
        f"/users/{user_id}",
        headers=admin_headers,
        json={"role": "agent", "department": "Operations"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "agent"
    assert body["department"] == "Operations"
