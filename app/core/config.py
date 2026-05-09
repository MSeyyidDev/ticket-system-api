"""Application settings loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="ticket-system-api")
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)

    jwt_secret: str = Field(default="dev-secret-change-me")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expires_minutes: int = Field(default=60)

    database_url: str = Field(default="sqlite:///./tickets.db")

    admin_email: str = Field(default="admin@example.com")
    admin_password: str = Field(default="admin123")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached accessor so the .env file is only parsed once per process."""
    return Settings()
