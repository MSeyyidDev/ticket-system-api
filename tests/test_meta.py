"""Tests for /tags, /categories, /stats, and Swagger metadata."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_categories_endpoint(client: TestClient) -> None:
    resp = client.get("/categories")
    assert resp.status_code == 200
    body = resp.json()
    assert "Hardware" in body and "Network" in body and "Other" in body


def test_tags_requires_auth(client: TestClient) -> None:
    resp = client.get("/tags")
    assert resp.status_code == 401


def test_tags_returns_list(client: TestClient, user_headers: dict[str, str]) -> None:
    # Create a ticket with tags so the listing has at least two entries.
    created = client.post(
        "/tickets",
        headers=user_headers,
        json={
            "title": "Ticket for tag test",
            "description": "A description with enough characters.\n\nMore.",
            "priority": "low",
            "category": "Other",
            "tags": ["browser", "license"],
        },
    )
    assert created.status_code == 201
    resp = client.get("/tags", headers=user_headers)
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()}
    assert {"browser", "license"}.issubset(names)


def test_stats_overview(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
) -> None:
    # Create a ticket and resolve it to populate the resolution-time aggregate.
    created = client.post(
        "/tickets",
        headers=user_headers,
        json={
            "title": "Stats walkthrough ticket",
            "description": "Some description text.\n\nWith two paragraphs.",
            "priority": "medium",
            "category": "Software",
        },
    )
    tid = created.json()["id"]
    for status in ("in_progress", "resolved"):
        client.post(
            f"/tickets/{tid}/status", headers=agent_headers, json={"status": status}
        )
    resp = client.get("/stats/overview", headers=user_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_tickets"] >= 1
    assert "open" in body["by_status"]
    assert body["total_users"] >= 3


def test_openapi_has_tags(client: TestClient) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec.get("paths", {})
    # Ensure key endpoints are documented.
    assert "/auth/login" in paths
    assert "/tickets" in paths
    assert "/stats/overview" in paths
