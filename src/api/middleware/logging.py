from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import get_logger

logger = get_logger(__name__)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Logs one structured line per request with latency and response code."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            request_id = getattr(request.state, "request_id", None)
            logger.info(
                "http_request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": getattr(response, "status_code", None) if response is not None else None,
                    "duration_ms": round(duration_ms, 2),
                },
            )
        if response is None:
            # If call_next raised, we still logged duration; re-raise by propagating a generic 500 response here
            # would hide the original exception. So we let the original exception propagate by raising.
            raise RuntimeError("Request failed before response was created")
        return response
