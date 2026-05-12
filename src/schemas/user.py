from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserCreate(BaseModel):
    """Payload to create a user."""

    email: EmailStr = Field(..., description="User email address")
    full_name: str | None = Field(default=None, description="User full name")


class UserRead(BaseModel):
    """User response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User id (UUID string)")
    email: EmailStr = Field(..., description="User email address")
    full_name: str | None = Field(default=None, description="User full name")
    created_at: str = Field(..., description="ISO timestamp of creation")
