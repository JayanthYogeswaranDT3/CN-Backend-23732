from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession as _AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.settings import get_settings

AsyncSession = _AsyncSession

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.db_echo,
    pool_size=_settings.db_pool_size,
    max_overflow=_settings.db_max_overflow,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# PUBLIC_INTERFACE
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that provides a request-scoped AsyncSession.

    Commits on success; rolls back on error; always closes the session.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
