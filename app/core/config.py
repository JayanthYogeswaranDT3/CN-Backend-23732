from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration loaded from environment variables.

    Uses Pydantic Settings v2 and supports `.env` in local development via `env_file`.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Career Navigator Backend", description="Application name")
    app_env: str = Field(default="local", description="Environment: local|staging|production")
    app_version: str = Field(default="0.1.0", description="Application version")

    log_level: str = Field(default="INFO", description="Logging level")

    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, description="Bind port")

    # DB
    database_url: str = Field(..., description="SQLAlchemy async database URL")

    # Security
    secret_key: str = Field(..., description="Secret key used for signing tokens, etc.")
    access_token_expire_minutes: int = Field(default=60, description="JWT access token lifetime")

    # CORS
    cors_origins: list[str] = Field(default_factory=list, description="Allowed CORS origins")

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
"
