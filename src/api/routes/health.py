from __future__ import annotations

from fastapi import APIRouter, status

from src.schemas.health import HealthResponse
from src.services.user_service import DatabasePingService

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Basic liveness probe (no external dependencies).",
)
async def health() -> HealthResponse:
    """Return a liveness signal indicating the API process is running."""
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Readiness probe (checks database connectivity).",
)
async def ready() -> HealthResponse:
    """Return readiness status after verifying critical dependencies (DB)."""
    ok = await DatabasePingService.ping()
    return HealthResponse(status="ok" if ok else "degraded")
