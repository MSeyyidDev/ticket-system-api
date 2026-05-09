"""User payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Common, mutable user fields."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=120)
    department: str | None = Field(default=None, max_length=80)
    role: UserRole = UserRole.REQUESTER


class UserCreate(UserBase):
    """Payload to create a new user."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "alice@example.com",
                    "full_name": "Alice Brown",
                    "department": "Finance",
                    "role": "requester",
                    "password": "s3cret-pass",
                }
            ]
        }
    )

    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Patch-style update — every field is optional."""

    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    department: str | None = Field(default=None, max_length=80)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(UserBase):
    """User representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
