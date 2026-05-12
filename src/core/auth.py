from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header
from fastapi.security.utils import get_authorization_scheme_param

from src.api.errors.exceptions import NotFoundError, UnauthorizedError
from src.db.session import AsyncSession, get_db_session
from src.models.user import User


@dataclass(frozen=True)
class TokenSubject:
    """Decoded token subject (prototype)."""

    user_id: str
    exp: int


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("utf-8"))


# PUBLIC_INTERFACE
def create_access_token(*, user_id: str, expires_in_seconds: int) -> str:
    """
    Create a simple unsigned bearer token (prototype only).

    This intentionally avoids adding JWT dependencies in the scaffold. The token
    is NOT tamper-proof and MUST be replaced with a signed JWT in production.

    Args:
        user_id: User id embedded as the subject.
        expires_in_seconds: Expiration window.

    Returns:
        str: A URL-safe token string.
    """
    payload = {"sub": user_id, "exp": int(time.time()) + int(expires_in_seconds)}
    return _b64url_encode(json.dumps(payload).encode("utf-8"))


def decode_access_token(token: str) -> TokenSubject:
    """Decode the prototype token and validate minimal fields."""
    try:
        raw = _b64url_decode(token)
        payload = json.loads(raw.decode("utf-8"))
        user_id = str(payload["sub"])
        exp = int(payload["exp"])
    except Exception as exc:
        raise UnauthorizedError("Invalid token") from exc

    if exp < int(time.time()):
        raise UnauthorizedError("Token expired")

    return TokenSubject(user_id=user_id, exp=exp)


# PUBLIC_INTERFACE
async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> User:
    """
    FastAPI dependency to resolve the authenticated user from a bearer token.

    Expects:
        Authorization: Bearer <token>

    Returns:
        User: The authenticated user.

    Raises:
        UnauthorizedError: If token missing/invalid/expired.
        NotFoundError: If the token subject user no longer exists.
    """
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")

    scheme, param = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer" or not param:
        raise UnauthorizedError("Invalid Authorization header")

    subject = decode_access_token(param)

    user = await db.get(User, subject.user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user
