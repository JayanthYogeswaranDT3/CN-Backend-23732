from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AuthRegisterRequest(BaseModel):
    """Request payload for registering a user and receiving an access token."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (prototype-only; not stored securely yet)")
    full_name: str | None = Field(default=None, description="Optional user display name")


class AuthLoginRequest(BaseModel):
    """Request payload for logging in and receiving an access token."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password (prototype-only; not stored securely yet)")


class TokenResponse(BaseModel):
    """OAuth2-like token response."""

    access_token: str = Field(..., description="Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")


class AuthResponse(BaseModel):
    """Register/login response including token + user."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(..., description="Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: dict = Field(..., description="User object (UserRead-compatible)")


class MeResponse(BaseModel):
    """Current authenticated user response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User id")
    email: EmailStr = Field(..., description="User email address")
    full_name: str | None = Field(default=None, description="Optional user full name")
