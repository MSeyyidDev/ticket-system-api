"""Authentication payloads."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials submitted by a client to obtain a JWT."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"email": "admin@example.com", "password": "admin123"}]
        }
    )

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT bearer token returned on successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds.")
