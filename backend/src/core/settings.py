from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables (12-factor friendly)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = Field(default="career-navigator-backend", description="Application name")
    environment: str = Field(default="local", description="local|staging|production")
    log_level: str = Field(default="INFO", description="Logging level")
    api_v1_prefix: str = Field(default="/api/v1", description="Prefix for v1 API routes")

    # Docs/CORS
    allow_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins.",
    )
    docs_enabled: bool = Field(default=True, description="Enable Swagger/ReDoc in this env")

    # DB (Postgres)
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="career_navigator", description="PostgreSQL database name")
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="postgres", description="PostgreSQL password")

    # SQLAlchemy
    db_echo: bool = Field(default=False, description="SQLAlchemy engine echo (SQL logs)")
    db_pool_size: int = Field(default=5, description="DB pool size")
    db_max_overflow: int = Field(default=10, description="DB pool max overflow")

    # Security placeholders
    secret_key: str = Field(default="change-me", description="Secret key for tokens/signing")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiration minutes")

    @property
    def allow_origins_list(self) -> list[str]:
        """Split allow_origins into a list (FastAPI expects list)."""
        return [o.strip() for o in self.allow_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        """
        SQLAlchemy async URL for Postgres.

        Note: uses asyncpg driver.
        """
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (safe because env vars are static per process)."""
    return Settings()
