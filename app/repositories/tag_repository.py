"""Database access for tags."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag import Tag


class TagRepository:
    """Single point of access for the ``tags`` table."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Tag]:
        stmt = select(Tag).order_by(Tag.name)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_name(self, name: str) -> Tag | None:
        stmt = select(Tag).where(Tag.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create_many(self, names: list[str]) -> list[Tag]:
        """Return existing or freshly created tag rows for the given names."""
        if not names:
            return []
        cleaned = sorted({n.strip().lower() for n in names if n and n.strip()})
        if not cleaned:
            return []

        existing = {
            t.name: t
            for t in self.db.execute(select(Tag).where(Tag.name.in_(cleaned))).scalars().all()
        }
        result: list[Tag] = []
        for name in cleaned:
            tag = existing.get(name)
            if tag is None:
                tag = Tag(name=name)
                self.db.add(tag)
            result.append(tag)
        self.db.flush()
        return result
