from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    """Generic pagination response wrapper."""

    items: list[T] = Field(default_factory=list, description="Returned items")
    total: int = Field(..., description="Total items count")
    limit: int = Field(..., description="Limit used for query")
    offset: int = Field(..., description="Offset used for query")
