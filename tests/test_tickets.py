"""Ticket CRUD, filtering, assignment and lifecycle tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_ticket(
    client: TestClient,
    headers: dict[str, str],
    *,
    title: str = "VPN keeps dropping",
    priority: str = "high",
    category: str = "Network",
    tags: list[str] | None = None,
) -> dict:
    payload = {
        "title": title,
        "description": "Two-paragraph description with details.\n\nMore context here.",
        "priority": priority,
        "category": category,
        "tags": tags or ["vpn", "wifi"],
    }
    resp = client.post("/tickets", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_ticket_as_requester(client: TestClient, user_headers: dict[str, str]) -> None:
    body = _create_ticket(client, user_headers)
    assert body["status"] == "open"
    assert body["priority"] == "high"
    assert body["category"] == "Network"
    assert {tag["name"] for tag in body["tags"]} == {"vpn", "wifi"}
    assert body["requester"]["email"] == "user@example.com"


def test_create_ticket_validation_error(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/tickets",
        headers=user_headers,
        json={"title": "no", "description": "", "priority": "high", "category": "Network"},
    )
    assert resp.status_code == 422


def test_list_and_filter_tickets(
    client: TestClient, user_headers: dict[str, str]
) -> None:
    _create_ticket(client, user_headers, title="Printer offline", category="Hardware", priority="low")
    _create_ticket(client, user_headers, title="Outlook crash", category="Email", priority="medium")
    resp = client.get("/tickets?category=Hardware", headers=user_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["category"] == "Hardware" for item in body["items"])
    assert body["total"] >= 1


def test_get_ticket_not_found(client: TestClient, user_headers: dict[str, str]) -> None:
    resp = client.get("/tickets/999999", headers=user_headers)
    assert resp.status_code == 404


def test_update_ticket_requires_agent(
    client: TestClient,
    user_headers: dict[str, str],
) -> None:
    created = _create_ticket(client, user_headers)
    resp = client.put(
        f"/tickets/{created['id']}",
        headers=user_headers,
        json={"priority": "critical"},
    )
    assert resp.status_code == 403


def test_update_ticket_as_agent(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
) -> None:
    created = _create_ticket(client, user_headers)
    resp = client.put(
        f"/tickets/{created['id']}",
        headers=agent_headers,
        json={"priority": "critical", "tags": ["vpn", "okta"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["priority"] == "critical"
    assert {t["name"] for t in body["tags"]} == {"okta", "vpn"}


def test_assign_ticket(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    created = _create_ticket(client, user_headers)
    # Find the agent's id.
    agents_resp = client.get("/users?page=1&page_size=200", headers=admin_headers)
    agent_id = next(
        u["id"] for u in agents_resp.json()["items"] if u["email"] == "agent@example.com"
    )
    resp = client.post(
        f"/tickets/{created['id']}/assign",
        headers=agent_headers,
        json={"assignee_id": agent_id},
    )
    assert resp.status_code == 200
    assert resp.json()["assignee"]["id"] == agent_id


def test_assign_requester_rejected(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    created = _create_ticket(client, user_headers)
    users_resp = client.get("/users?page=1&page_size=200", headers=admin_headers)
    requester_id = next(
        u["id"] for u in users_resp.json()["items"] if u["email"] == "user@example.com"
    )
    resp = client.post(
        f"/tickets/{created['id']}/assign",
        headers=agent_headers,
        json={"assignee_id": requester_id},
    )
    assert resp.status_code == 400


def test_status_transition_happy_path(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
) -> None:
    created = _create_ticket(client, user_headers)
    tid = created["id"]
    for target in ("in_progress", "resolved", "closed"):
        resp = client.post(
            f"/tickets/{tid}/status", headers=agent_headers, json={"status": target}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == target
    final = client.get(f"/tickets/{tid}", headers=user_headers).json()
    assert final["resolved_at"] is not None


def test_status_transition_invalid(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
) -> None:
    created = _create_ticket(client, user_headers)
    resp = client.post(
        f"/tickets/{created['id']}/status",
        headers=agent_headers,
        json={"status": "resolved"},  # cannot jump from open straight to resolved
    )
    assert resp.status_code == 409


def test_delete_ticket_requires_agent(
    client: TestClient,
    user_headers: dict[str, str],
    agent_headers: dict[str, str],
) -> None:
    created = _create_ticket(client, user_headers)
    forbidden = client.delete(f"/tickets/{created['id']}", headers=user_headers)
    assert forbidden.status_code == 403
    ok = client.delete(f"/tickets/{created['id']}", headers=agent_headers)
    assert ok.status_code == 204
    missing = client.get(f"/tickets/{created['id']}", headers=user_headers)
    assert missing.status_code == 404
