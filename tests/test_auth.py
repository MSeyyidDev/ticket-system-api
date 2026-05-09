"""Authentication-related tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_success(client: TestClient) -> None:
    resp = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0


def test_login_wrong_password(client: TestClient) -> None:
    resp = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password."


def test_login_unknown_user(client: TestClient) -> None:
    resp = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "whatever"}
    )
    assert resp.status_code == 401


def test_login_invalid_payload(client: TestClient) -> None:
    resp = client.post("/auth/login", json={"email": "not-an-email", "password": "x"})
    assert resp.status_code == 422


def test_protected_route_requires_token(client: TestClient) -> None:
    resp = client.get("/users")
    assert resp.status_code == 401


def test_protected_route_rejects_garbage_token(client: TestClient) -> None:
    resp = client.get("/users", headers={"Authorization": "Bearer not.a.real.jwt"})
    assert resp.status_code == 401


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
