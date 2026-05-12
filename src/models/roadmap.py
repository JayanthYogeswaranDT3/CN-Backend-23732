from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import CreatedByMixin, SoftDeleteMixin, TimestampAuditMixin, UUIDPrimaryKeyMixin


class Roadmap(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin, CreatedByMixin, SoftDeleteMixin):
    """A user-owned roadmap, typically for a selected career path.

    Matches `roadmaps` in the Postgres MVP schema.
    """

    __tablename__ = "roadmaps"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    career_path_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("career_paths.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    selection_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("user_career_path_selections.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    user = relationship("User", back_populates="roadmaps")
    career_path = relationship("CareerPath")
    selection = relationship("UserCareerPathSelection")
    milestones = relationship("Milestone", back_populates="roadmap", cascade="all, delete-orphan")
    marketplace_links = relationship("RoadmapMarketplaceItem", back_populates="roadmap", cascade="all, delete-orphan")


Index("ix_roadmaps_user_status", Roadmap.user_id, Roadmap.status)


class Milestone(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Top-level roadmap milestone.

    Matches `milestones` in the Postgres MVP schema.
    """

    __tablename__ = "milestones"

    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    milestone_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    roadmap = relationship("Roadmap", back_populates="milestones")
    tasks = relationship("MilestoneTask", back_populates="milestone", cascade="all, delete-orphan")
    marketplace_links = relationship("MilestoneMarketplaceItem", back_populates="milestone", cascade="all, delete-orphan")


Index("ix_milestones_roadmap_complete", Milestone.roadmap_id, Milestone.is_complete)


class MilestoneTask(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Optional finer-grained task within a milestone.

    Matches `milestone_tasks` in the Postgres MVP schema.
    """

    __tablename__ = "milestone_tasks"

    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    milestone = relationship("Milestone", back_populates="tasks")


Index("ix_milestone_tasks_milestone_complete", MilestoneTask.milestone_id, MilestoneTask.is_complete)

