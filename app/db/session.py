from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    """Initialize the async engine and sessionmaker.

    Called during FastAPI startup.
    """
    global _engine, _sessionmaker
    settings = get_settings()
    _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    _sessionmaker = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def close_engine() -> None:
    """Dispose the engine.

    Called during FastAPI shutdown.
    """
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession per request."""
    if _sessionmaker is None:
        # Defensive: startup should have initialized this
        init_engine()

    assert _sessionmaker is not None
    async with _sessionmaker() as session:
        yield session
"
