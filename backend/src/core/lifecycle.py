from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.logging import configure_logging
from src.core.settings import get_settings
from src.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan manager.

    - Configures logging early.
    - Optionally initializes DB (safe idempotent operations only).
    """
    configure_logging()
    _ = get_settings()

    # In real production apps you typically *do not* auto-run migrations here.
    # init_db is intentionally minimal and idempotent.
    await init_db()

    yield
