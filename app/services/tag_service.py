"""Tag business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository


class TagService:
    """Read-only tag operations exposed to the API layer."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tags = TagRepository(db)

    def list(self) -> list[Tag]:
        return self.tags.list()
