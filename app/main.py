"""FastAPI application factory and entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.core.config import get_settings
from app.core.database import init_db
from app.routers import auth, categories, comments, stats, tags, tickets, users

logger = logging.getLogger("ticket_system_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - exercised by uvicorn
    """Run startup hooks (table creation) and yield to serve traffic."""
    settings = get_settings()
    logger.info("Starting %s in %s mode (db=%s)", settings.app_name, settings.app_env, settings.database_url)
    init_db()
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    app = FastAPI(
        title="Ticket System API",
        description=(
            "A clean, production-style REST API for an IT support ticketing system. "
            "Layered architecture (models / schemas / repositories / services / routers), "
            "JWT auth, state-machine-validated ticket lifecycle, and rich seeded data."
        ),
        version=__version__,
        lifespan=lifespan,
        contact={"name": "Seyyid Sahin", "email": "seyyidsahin2834@gmail.com"},
        license_info={"name": "MIT", "identifier": "MIT"},
    )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(tickets.router)
    app.include_router(comments.router)
    app.include_router(tags.router)
    app.include_router(categories.router)
    app.include_router(stats.router)

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
