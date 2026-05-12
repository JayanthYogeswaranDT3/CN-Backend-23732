from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health response payload."""

    status: str = Field(..., description="ok|degraded")
