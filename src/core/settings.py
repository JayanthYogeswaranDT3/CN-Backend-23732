from __future__ import annotations

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
    postgres_connection: str | None = Field(
        default=None,
        description=(
            "Optional full Postgres connection URI. Preferred when set. "
            "Example (Neon): postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
        ),
    )
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

    def _normalize_to_asyncpg_sqlalchemy_scheme(self, raw: str) -> str:
        """
        Normalize a raw postgres URI to SQLAlchemy asyncpg scheme.

        Accepts:
        - postgresql+asyncpg://...
        - postgresql://...
        - postgres://...

        Returns:
            str: URL starting with postgresql+asyncpg:// (or raw if unrecognized).
        """
        if raw.startswith("postgresql+asyncpg://"):
            return raw
        if raw.startswith("postgresql://"):
            return "postgresql+asyncpg://" + raw[len("postgresql://") :]
        if raw.startswith("postgres://"):
            return "postgresql+asyncpg://" + raw[len("postgres://") :]
        return raw

    def _split_and_clean_query_params(self, url: str) -> tuple[str, dict[str, str]]:
        """
        Remove libpq-only params that asyncpg does not understand from the URL query.

        Neon connection strings often include libpq parameters like:
        - sslmode=require
        - channel_binding=require

        asyncpg (used by SQLAlchemy's asyncpg dialect) does NOT accept these as
        connect kwargs and will raise:
            TypeError: connect() got an unexpected keyword argument 'sslmode'

        We therefore strip these parameters from the URL and return them separately
        so we can configure SSL explicitly via connect_args in engine creation.

        Returns:
            (clean_url, original_query_dict)
        """
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))

        # Strip libpq-only params that should not be passed through SQLAlchemy URL.
        # Keep the rest (if any) intact.
        for k in ("sslmode", "channel_binding"):
            query.pop(k, None)

        clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
        return clean_url, dict(parse_qsl(parts.query, keep_blank_values=True))

    @property
    def database_url(self) -> str:
        """
        SQLAlchemy async URL for Postgres.

        IMPORTANT:
        - Uses asyncpg driver.
        - Must NOT include libpq-only query params (e.g., sslmode, channel_binding),
          because SQLAlchemy's asyncpg dialect will forward them into asyncpg.connect()
          causing TypeError.
        - SSL is configured separately via `database_connect_args`.
        """
        # Prefer a single connection URI if provided (e.g., Neon, managed Postgres).
        if self.postgres_connection:
            raw = self.postgres_connection.strip()
            normalized = self._normalize_to_asyncpg_sqlalchemy_scheme(raw)
            clean_url, _ = self._split_and_clean_query_params(normalized)
            return clean_url

        # Fall back to discrete host/port/db/user/password configuration.
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_connect_args(self) -> dict:
        """
        Extra connect args for SQLAlchemy engine creation.

        For Neon (and many managed Postgres providers), SSL must be enabled.
        Because asyncpg does not accept libpq-style `sslmode`, we configure SSL
        explicitly via `connect_args={"ssl": True}`.

        Decision logic:
        - If POSTGRES_CONNECTION contains sslmode=require/verify-ca/verify-full,
          enable SSL.
        - If POSTGRES_CONNECTION has no sslmode, we still enable SSL by default
          because managed providers commonly require it.
        - For local/discrete settings (no POSTGRES_CONNECTION), do not enable SSL
          by default.
        """
        if not self.postgres_connection:
            return {}

        raw = self.postgres_connection.strip()
        normalized = self._normalize_to_asyncpg_sqlalchemy_scheme(raw)
        _, original_query = self._split_and_clean_query_params(normalized)

        sslmode = (original_query.get("sslmode") or "").strip().lower()

        # If sslmode is explicitly disabling SSL, honor it (rare for Neon).
        if sslmode in {"disable", "allow", "prefer"}:
            return {}

        # For require/verify-* OR missing sslmode on managed URI -> enable SSL.
        return {"ssl": True}


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (safe because env vars are static per process)."""
    return Settings()
