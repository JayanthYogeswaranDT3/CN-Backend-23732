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

    # Track DB readiness without preventing API startup.
    # This ensures the API can still serve non-DB endpoints even if the DB is down/misconfigured.
    app.state.db_ready = False
    app.state.db_init_error = None

    # In real production apps you typically *do not* auto-run migrations here.
    # init_db is intentionally minimal and idempotent. If it fails, we keep running.
    try:
        await init_db()
        app.state.db_ready = True
    except Exception as exc:  # noqa: BLE001 - we want to capture any startup DB failure
        app.state.db_ready = False
        app.state.db_init_error = str(exc)

    yield

    # No explicit shutdown action required; SQLAlchemy engine will be GC'd.
