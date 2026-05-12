from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from src.api.errors.exceptions import ConflictError, NotFoundError, ValidationError
from src.core.logging import get_logger

logger = get_logger(__name__)


def _error_payload(request: Request, code: str, message: str) -> dict:
    request_id = getattr(request.state, "request_id", None)
    return {"error": {"code": code, "message": message, "request_id": request_id}}


# PUBLIC_INTERFACE
def install_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers for consistent error responses."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        logger.info("not_found", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_error_payload(request, "not_found", str(exc) or "Not found"),
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        logger.info("conflict", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_payload(request, "conflict", str(exc) or "Conflict"),
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        logger.info("validation_error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload(request, "validation_error", str(exc) or "Invalid input"),
        )
