"""Shared pytest fixtures.

Spins up a fresh, isolated SQLite database and a corresponding TestClient for
each test module. Seeded users:

  * admin@example.com  / admin123     (admin)
  * agent@example.com  / agent123     (agent)
  * user@example.com   / user1234     (requester)
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Point the application at an isolated test database BEFORE any app import.
TEST_DB_PATH = Path(__file__).resolve().parent / "test_tickets.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "test-secret-do-not-use-in-prod"

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

# Local imports happen after env vars are set so the cached settings see them.
from app.core import database as db_module  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

# Build a dedicated engine/session bound to the test DB and override the
# application's defaults so every dependency resolves against this DB.
test_engine = create_engine(
    f"sqlite:///{TEST_DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
    future=True,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False, future=True
)

# Patch the module-level engine/SessionLocal so init_db() and any direct
# imports use the test database too.
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal


def _override_get_db() -> Iterator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _prepare_database() -> Iterator[None]:
    """Create tables once per test session and seed the canonical users."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        db.add_all(
            [
                User(
                    email="admin@example.com",
                    full_name="Test Admin",
                    department="IT",
                    role=UserRole.ADMIN,
                    hashed_password=hash_password("admin123"),
                ),
                User(
                    email="agent@example.com",
                    full_name="Test Agent",
                    department="IT",
                    role=UserRole.AGENT,
                    hashed_password=hash_password("agent123"),
                ),
                User(
                    email="user@example.com",
                    full_name="Test Requester",
                    department="Sales",
                    role=UserRole.REQUESTER,
                    hashed_password=hash_password("user1234"),
                ),
            ]
        )
        db.commit()
    finally:
        db.close()
    yield
    try:
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except (OSError, PermissionError):
        # On Windows the SQLite file may still be held by a worker; ignore.
        pass


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """A TestClient bound to a fresh FastAPI app with the DB override."""
    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    return _login(client, "admin@example.com", "admin123")


@pytest.fixture()
def agent_token(client: TestClient) -> str:
    return _login(client, "agent@example.com", "agent123")


@pytest.fixture()
def user_token(client: TestClient) -> str:
    return _login(client, "user@example.com", "user1234")


@pytest.fixture()
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def agent_headers(agent_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {agent_token}"}


@pytest.fixture()
def user_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}
