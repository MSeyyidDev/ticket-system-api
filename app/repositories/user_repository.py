"""Database access for users."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


class UserRepository:
    """Single point of access for ``users`` table operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- queries ----------------------------------------------------------------

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, *, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        offset = (page - 1) * page_size
        total = self.db.execute(select(func.count(User.id))).scalar_one()
        stmt = select(User).order_by(User.id).offset(offset).limit(page_size)
        items = list(self.db.execute(stmt).scalars().all())
        return items, int(total)

    def count_by_role(self) -> dict[str, int]:
        stmt = select(User.role, func.count(User.id)).group_by(User.role)
        return {role.value: count for role, count in self.db.execute(stmt).all()}

    def count(self) -> int:
        return int(self.db.execute(select(func.count(User.id))).scalar_one())

    # --- mutations --------------------------------------------------------------

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def first_agent_or_admin(self) -> User | None:
        stmt = (
            select(User)
            .where(User.role.in_([UserRole.AGENT, UserRole.ADMIN]))
            .order_by(User.id)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()
