from __future__ import annotations

from fastapi import HTTPException, status


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""


class ConflictError(Exception):
    """Raised when a resource already exists or violates constraints."""


def http_404(detail: str) -> HTTPException:
    """Create a standardized 404 HTTPException."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def http_409(detail: str) -> HTTPException:
    """Create a standardized 409 HTTPException."""
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
"
