"""Comment endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_ticket(client: TestClient, headers: dict[str, str]) -> int:
    resp = client.post(
        "/tickets",
        headers=headers,
        json={
            "title": "Need help with VPN",
            "description": "It disconnects intermittently.\n\nLogs attached.",
            "priority": "medium",
            "category": "Network",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_add_and_list_comments(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
) -> None:
    ticket_id = _create_ticket(client, user_headers)
    add = client.post(
        f"/tickets/{ticket_id}/comments",
        headers=agent_headers,
        json={"body": "Looking into this now.", "is_internal": False},
    )
    assert add.status_code == 201
    listing = client.get(f"/tickets/{ticket_id}/comments", headers=user_headers)
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == 1
    assert items[0]["body"] == "Looking into this now."
    assert items[0]["author"]["email"] == "agent@example.com"


def test_comment_on_missing_ticket(
    client: TestClient, agent_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/tickets/999999/comments",
        headers=agent_headers,
        json={"body": "Hi", "is_internal": True},
    )
    assert resp.status_code == 404


def test_comment_validation_error(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    ticket_id = _create_ticket(client, user_headers)
    resp = client.post(
        f"/tickets/{ticket_id}/comments",
        headers=user_headers,
        json={"body": "", "is_internal": False},
    )
    assert resp.status_code == 422
