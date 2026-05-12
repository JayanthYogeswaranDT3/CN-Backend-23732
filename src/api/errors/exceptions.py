from __future__ import annotations


class AppError(Exception):
    """Base exception type for application errors."""


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""


class ConflictError(AppError):
    """Raised when a uniqueness conflict or similar constraint is violated."""


class ValidationError(AppError):
    """Raised when business validation fails (not request schema validation)."""


class UnauthorizedError(AppError):
    """Raised when authentication fails or user is not authorized."""
