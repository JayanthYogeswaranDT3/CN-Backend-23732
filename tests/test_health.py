from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_health_check() -> None:
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
"
