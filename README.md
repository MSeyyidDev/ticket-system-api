# ticket-system-api

[![CI](https://github.com/MSeyyidDev/ticket-system-api/actions/workflows/ci.yml/badge.svg)](https://github.com/MSeyyidDev/ticket-system-api/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A clean, production-style REST API for an IT support ticketing system, written in Python with FastAPI and SQLAlchemy 2.0.

This project demonstrates how to design and ship a non-trivial REST API: a layered, testable architecture with proper authentication, a state-machine-validated ticket lifecycle, rich filtering and pagination, and a generous synthetic data set so the analytics surface is never empty.

It is deliberately self-contained — SQLite, no Docker, no managed services — so a reviewer can clone it and have a working server with thousands of realistic tickets in under a minute.

## Highlights

- FastAPI with tagged routers, summaries, and request examples — Swagger UI at `/docs` is browseable.
- Clean layered architecture: `models` (SQLAlchemy), `schemas` (Pydantic v2), `repositories`, `services`, `routers`. No god files.
- JWT bearer auth (`python-jose`) with role-based dependencies (`requester`, `agent`, `admin`).
- State machine on ticket status — invalid transitions return `409 Conflict` with a precise message.
- Powerful list endpoint: filter by status / priority / category / assignee / requester, free-text search, sortable, paginated.
- Synthetic seed: 100 users, 1,000 tickets spanning 12 months, 5,000-8,000 comments, 20 tags, realistic IT-support tone.
- 28+ pytest tests covering happy and unhappy paths against an isolated SQLite test database.
- Project hygiene: pinned `requirements.txt`, `pyproject.toml`, `.env.example`, `Makefile`, MIT licence.

## Architecture

```
                   +---------------------------+
   HTTP client --->|  FastAPI app (app/main.py)|
                   +-------------+-------------+
                                 |
                                 v
                   +---------------------------+
                   | Routers (app/routers/*)   |
                   | auth users tickets ...    |
                   +-------------+-------------+
                                 |
                                 v
                   +---------------------------+
                   | Services (business logic) |
                   | Ticket lifecycle, auth,   |
                   | stats, comments, tags     |
                   +-------------+-------------+
                                 |
                                 v
                   +---------------------------+
                   | Repositories (queries)    |
                   | SQLAlchemy 2.0 sessions   |
                   +-------------+-------------+
                                 |
                                 v
                   +---------------------------+
                   |  SQLite database          |
                   +---------------------------+
```

Pydantic v2 schemas live alongside the layers above and form the public API contract.

## Tech stack

| Concern        | Choice                                |
| -------------- | ------------------------------------- |
| Web framework  | FastAPI 0.115                         |
| ORM            | SQLAlchemy 2.0 (declarative, typed)   |
| Validation     | Pydantic v2 + `pydantic-settings`     |
| Auth           | JWT via `python-jose`, `passlib[bcrypt]` |
| Database       | SQLite (file-based, portable)         |
| Server         | Uvicorn                               |
| Synthetic data | Faker                                 |
| Tests          | pytest + httpx + FastAPI TestClient   |

## Project layout

```
ticket-system-api/
├── app/
│   ├── core/           # config, database, security, dependencies
│   ├── models/         # SQLAlchemy ORM classes
│   ├── schemas/        # Pydantic request/response models
│   ├── repositories/   # query objects (one per aggregate)
│   ├── services/       # business logic
│   ├── routers/        # FastAPI routers
│   ├── main.py         # application factory
│   └── seed.py         # synthetic data generator
├── tests/              # pytest suite (isolated SQLite DB)
├── docs/screenshots/   # placeholder for Swagger UI screenshots
├── requirements.txt
├── pyproject.toml
├── Makefile
├── LICENSE
└── README.md
```

## Setup

> Requires Python 3.11+. The project was developed against Python 3.13.

### Using `pip` + `venv` (recommended for portability)

```bash
git clone https://github.com/seyyidsahin2834/ticket-system-api.git
cd ticket-system-api

python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env   # then edit if you wish
```

### Using `uv` (fast alternative)

```bash
uv venv
uv pip install -r requirements.txt
```

## Seed the database

```bash
python -m app.seed
```

You should see something like:

```
INFO seed :: Seeding 100 users ...
INFO seed :: Seeding 20 tags ...
INFO seed :: Seeding 1000 tickets ...
INFO seed :: Seeding comments ...
INFO seed :: Done. users=100 tags=20 tickets=1000 comments=~5500
```

The seed is idempotent — running it again wipes the database first and rebuilds it from a fixed random seed for reproducible demos.

## Run the server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# or:
make run
```

Then open:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc:      http://127.0.0.1:8000/redoc
- OpenAPI:    http://127.0.0.1:8000/openapi.json

The seeded admin credentials are `admin@example.com` / `admin123` (override via `.env`).

## Run the tests

```bash
pytest -v
# or:
make test
```

The suite uses its own SQLite file under `tests/test_tickets.db`, recreated per session.

## Endpoint table

| Method | Path                                | Auth         | Description                                  |
| ------ | ----------------------------------- | ------------ | -------------------------------------------- |
| POST   | `/auth/login`                       | public       | Exchange email + password for a JWT          |
| GET    | `/health`                           | public       | Liveness probe                               |
| GET    | `/users`                            | any user     | List users (paginated)                       |
| POST   | `/users`                            | admin        | Create a user                                |
| GET    | `/users/{id}`                       | any user     | Fetch a user                                 |
| PUT    | `/users/{id}`                       | admin        | Update a user                                |
| DELETE | `/users/{id}`                       | admin        | Delete a user                                |
| GET    | `/tickets`                          | any user     | List tickets, filter / sort / paginate       |
| POST   | `/tickets`                          | any user     | Open a new ticket                            |
| GET    | `/tickets/{id}`                     | any user     | Fetch a ticket                               |
| PUT    | `/tickets/{id}`                     | agent/admin  | Update title / description / tags / priority |
| DELETE | `/tickets/{id}`                     | agent/admin  | Delete a ticket                              |
| POST   | `/tickets/{id}/assign`              | agent/admin  | Assign / unassign agent                      |
| POST   | `/tickets/{id}/status`              | agent/admin  | Move through state machine                   |
| GET    | `/tickets/{id}/comments`            | any user     | List comments on a ticket                    |
| POST   | `/tickets/{id}/comments`            | any user     | Post a comment                               |
| GET    | `/tags`                             | any user     | List every tag                               |
| GET    | `/categories`                       | public       | List supported categories                    |
| GET    | `/stats/overview`                   | any user     | KPIs across the data set                     |

### Ticket status machine

```
open ──> in_progress ──> resolved ──> closed
  │           │               ▲
  │           v               │
  └──> pending <──────────────┘
```

Any other transition returns `409 Conflict`.

## Example requests

### Login

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Open a ticket

```bash
TOKEN=...
curl -s -X POST http://127.0.0.1:8000/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
        "title": "VPN keeps dropping",
        "description": "Disconnects every few minutes...\n\nReboot did not help.",
        "priority": "high",
        "category": "Network",
        "tags": ["vpn","wifi"]
      }'
```

### Filter / paginate

```bash
curl -s -G http://127.0.0.1:8000/tickets \
  --data-urlencode "status=in_progress" \
  --data-urlencode "priority=critical" \
  --data-urlencode "sort=-priority" \
  --data-urlencode "page=1" \
  --data-urlencode "page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Stats overview

```bash
curl -s http://127.0.0.1:8000/stats/overview -H "Authorization: Bearer $TOKEN"
```

```json
{
  "total_tickets": 1000,
  "open_tickets": 200,
  "resolved_tickets": 250,
  "closed_tickets": 200,
  "by_status": { "open": 200, "in_progress": 250, "pending": 100, "resolved": 250, "closed": 200 },
  "by_priority": { "low": 300, "medium": 400, "high": 200, "critical": 100 },
  "by_category": { "Hardware": 145, "Software": 152, "Network": 142, "Account": 138, "Email": 144, "Security": 138, "Other": 141 },
  "average_resolution_hours": 26.4,
  "total_users": 100,
  "total_comments": 5497
}
```

## Screenshots

> Swagger UI screenshot lives at `docs/screenshots/swagger.png`. To capture it, run the server (`make run`) and take a screenshot of `http://127.0.0.1:8000/docs`. A `.gitkeep` file is committed in the meantime.

## Development tasks

```bash
make install   # create venv and install deps
make seed      # populate the database
make run       # start the dev server with autoreload
make test      # run pytest
make lint      # quick syntax check
make clean     # remove caches and the SQLite database
```

## License

MIT - see [LICENSE](LICENSE).
