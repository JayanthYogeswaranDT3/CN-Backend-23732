from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import SkillLevel, TimestampAuditMixin, UUIDPrimaryKeyMixin


class CareerPath(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Platform-level career path catalog item.

    Matches `career_paths` in the Postgres MVP schema.
    """

    __tablename__ = "career_paths"

    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    skills = relationship("CareerPathSkill", back_populates="career_path", cascade="all, delete-orphan")


class CareerPathSkill(Base):
    """Junction defining skill requirements/targets for a career path.

    Matches `career_path_skills` in the Postgres MVP schema.
    Composite primary key: (career_path_id, skill_id)
    """

    __tablename__ = "career_path_skills"

    career_path_id: Mapped[str] = mapped_column(
        ForeignKey("career_paths.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[str] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )

    target_level: Mapped[Optional[SkillLevel]] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    weight: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    career_path = relationship("CareerPath", back_populates="skills")
    skill = relationship("Skill", back_populates="career_path_links")


class CareerPathRecommendation(Base, UUIDPrimaryKeyMixin):
    """System-generated career path recommendation for a user.

    Matches `career_path_recommendations` in the Postgres MVP schema.
    """

    __tablename__ = "career_path_recommendations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    career_path_id: Mapped[str] = mapped_column(ForeignKey("career_paths.id", ondelete="RESTRICT"), nullable=False, index=True)

    assessment_run_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("skill_assessment_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    fit_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="career_path_recommendations")
    career_path = relationship("CareerPath")
    assessment_run = relationship("SkillAssessmentRun")


Index("ix_career_path_recommendations_user_fit_score", CareerPathRecommendation.user_id, CareerPathRecommendation.fit_score.desc())


class UserCareerPathSelection(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """User's selected career path.

    Matches `user_career_path_selections` in the Postgres MVP schema.
    """

    __tablename__ = "user_career_path_selections"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    career_path_id: Mapped[str] = mapped_column(ForeignKey("career_paths.id", ondelete="RESTRICT"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="career_path_selections")
    career_path = relationship("CareerPath")

