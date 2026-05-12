from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


def _uuid_str() -> str:
    """Generate a UUID4 string.

    Note: Existing backend scaffold uses string IDs (String(36)) for users.
    For consistency across the codebase, the MVP schema's UUID columns are
    represented as String(36) containing canonical UUID text.
    """
    return str(uuid4())


class SkillLevel(str, Enum):
    """Represents the 'skill_level' enum from the Postgres MVP schema."""

    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class DashboardPhase(str, Enum):
    """Represents the 'dashboard_phase' enum from the Postgres MVP schema."""

    build_profile = "build_profile"
    skill_assessment = "skill_assessment"
    career_paths = "career_paths"
    roadmap = "roadmap"
    marketplace = "marketplace"


class PhaseStatus(str, Enum):
    """Represents the 'phase_status' enum from the Postgres MVP schema."""

    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    locked = "locked"


class DocumentType(str, Enum):
    """Represents the 'document_type' enum from the Postgres MVP schema."""

    resume = "resume"
    certificate = "certificate"
    job_description = "job_description"
    portfolio = "portfolio"
    other = "other"


class MarketplaceItemType(str, Enum):
    """Represents the 'marketplace_item_type' enum from the Postgres MVP schema."""

    course = "course"
    certification = "certification"
    job = "job"
    other = "other"


class UUIDPrimaryKeyMixin:
    """Mixin providing a UUID string primary key."""
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)


class TimestampAuditMixin:
    """Mixin providing created_at/updated_at timestamp audit fields.

    The DB schema uses triggers for updated_at in Postgres. In the ORM layer we
    use onupdate so updated_at changes even without triggers.
    """
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=datetime.utcnow,
    )


class CreatedByMixin:
    """Mixin for created_by FK audit field (nullable)."""
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class SoftDeleteMixin:
    """Mixin providing soft delete fields (deleted_at/deleted_by)."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class IsActiveMixin:
    """Mixin providing is_active boolean used by some catalog/state tables."""
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

