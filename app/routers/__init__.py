"""FastAPI routers — the HTTP layer."""

from app.routers import auth, categories, comments, stats, tags, tickets, users

__all__ = ["auth", "categories", "comments", "stats", "tags", "tickets", "users"]
