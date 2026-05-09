"""User business logic."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserRead, UserUpdate


class UserService:
    """High-level user management operations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def create(self, payload: UserCreate) -> User:
        if self.users.get_by_email(str(payload.email)) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )
        user = User(
            email=str(payload.email),
            full_name=payload.full_name,
            department=payload.department,
            role=payload.role,
            hashed_password=hash_password(payload.password),
        )
        self.users.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:  # pragma: no cover - defensive
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already exists."
            ) from exc
        self.db.refresh(user)
        return user

    def list(self, *, page: int, page_size: int) -> Page[UserRead]:
        items, total = self.users.list(page=page, page_size=page_size)
        return Page[UserRead](
            items=[UserRead.model_validate(u) for u in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    def update(self, user_id: int, payload: UserUpdate) -> User:
        user = self.get(user_id)
        data = payload.model_dump(exclude_unset=True)
        if "password" in data and data["password"] is not None:
            user.hashed_password = hash_password(data.pop("password"))
        else:
            data.pop("password", None)
        for field, value in data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> None:
        user = self.get(user_id)
        # Soft-protect users that already have tickets — deleting would break FKs.
        if user.requested_tickets:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete a user that has requested tickets.",
            )
        self.users.delete(user)
        self.db.commit()
