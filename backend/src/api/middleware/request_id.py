from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.utils.ids import new_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Adds an X-Request-ID header to every request/response.

    If the client provides X-Request-ID, it is preserved.
    Otherwise, a new id is generated.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
