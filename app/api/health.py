from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Basic liveness endpoint for load balancers and uptime checks.",
    operation_id="health_check",
)
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A small JSON payload indicating the service is up.
    """
    return {"status": "ok"}
"
