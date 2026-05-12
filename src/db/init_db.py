from __future__ import annotations

from sqlalchemy import text

from src.db.session import engine


# PUBLIC_INTERFACE
async def init_db() -> None:
    """
    Minimal DB initialization.

    This is intentionally conservative:
    - verifies the DB connection works
    - does not auto-create tables (migrations should manage schema in real deployments)
    """
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
