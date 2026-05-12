from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_openapi_available() -> None:
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "paths" in data
    assert "/health" in data["paths"]
"
