from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from src.api.errors.exceptions import ConflictError, UnauthorizedError
from src.core.auth import create_access_token, get_current_user
from src.core.security import hash_password
from src.core.settings import get_settings
from src.db.session import AsyncSession, get_db_session
from src.models.user import User
from src.schemas.auth import AuthLoginRequest, AuthRegisterRequest, AuthResponse, MeResponse
from src.schemas.user import UserRead
from src.utils.ids import new_uuid

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    description="Creates a user account and returns a bearer token (prototype auth).",
    operation_id="auth_register",
)
async def register(
    payload: AuthRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """Register a new user and return a bearer token (prototype)."""
    # Prototype-only: we do not persist password hash in DB yet (users table has no password column).
    # We still hash it to avoid logging/handling raw text, but it is not stored.
    _ = hash_password(payload.password)

    existing = await db.execute(select(User).where(User.email == str(payload.email)))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("User with this email already exists")

    user = User(id=new_uuid(), email=str(payload.email), full_name=payload.full_name)
    db.add(user)
    await db.flush()

    settings = get_settings()
    token = create_access_token(user_id=user.id, expires_in_seconds=settings.access_token_expire_minutes * 60)

    return AuthResponse(access_token=token, token_type="bearer", user=UserRead.model_validate(user).model_dump())


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Logs in an existing user by email (prototype). Returns a bearer token.",
    operation_id="auth_login",
)
async def login(
    payload: AuthLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """Login and return a bearer token (prototype)."""
    # Prototype-only: since passwords aren't persisted, accept login if email exists.
    # Still hash to avoid handling raw password further.
    _ = hash_password(payload.password)

    res = await db.execute(select(User).where(User.email == str(payload.email)))
    user = res.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Invalid credentials")

    settings = get_settings()
    token = create_access_token(user_id=user.id, expires_in_seconds=settings.access_token_expire_minutes * 60)

    return AuthResponse(access_token=token, token_type="bearer", user=UserRead.model_validate(user).model_dump())


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Returns the current authenticated user identity.",
    operation_id="auth_me",
)
async def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """Return the current authenticated user."""
    return MeResponse.model_validate(current_user)
