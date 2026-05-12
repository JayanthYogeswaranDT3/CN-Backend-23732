from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ItemBase(BaseModel):
    """Shared fields for item DTOs."""

    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    description: str | None = Field(default=None, max_length=1000, description="Optional description")


class ItemCreate(ItemBase):
    """Payload for creating an item."""


class ItemUpdate(BaseModel):
    """Payload for updating an item (partial update)."""

    name: str | None = Field(default=None, min_length=1, max_length=200, description="Item name")
    description: str | None = Field(default=None, max_length=1000, description="Optional description")


class ItemRead(ItemBase):
    """Response DTO for an item."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Item id")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
"
