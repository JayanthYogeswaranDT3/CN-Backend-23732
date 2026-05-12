from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import SkillLevel, TimestampAuditMixin, UUIDPrimaryKeyMixin


class SkillAssessmentRun(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """A combined assessment event for a user.

    Matches `skill_assessment_runs` in the Postgres MVP schema.
    """

    __tablename__ = "skill_assessment_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    persona_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("persona_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    questionnaire_response_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("questionnaire_responses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(64), nullable=False, default="completed")

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # There are two FKs to users.id (user_id and created_by). Disambiguate explicitly.
    user = relationship("User", back_populates="skill_assessment_runs", foreign_keys=[user_id])
    persona = relationship("PersonaProfile")
    questionnaire_response = relationship("QuestionnaireResponse", back_populates="assessment_runs")
    results = relationship("SkillAssessmentSkillResult", back_populates="assessment_run", cascade="all, delete-orphan")


class SkillAssessmentSkillResult(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Per-skill result of an assessment run.

    Matches `skill_assessment_skill_results` in the Postgres MVP schema.
    """

    __tablename__ = "skill_assessment_skill_results"

    assessment_run_id: Mapped[str] = mapped_column(
        ForeignKey("skill_assessment_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    final_level: Mapped[Optional[SkillLevel]] = mapped_column(String(32), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3), nullable=True)
    missing_evidence: Mapped[bool] = mapped_column(nullable=False, default=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    assessment_run = relationship("SkillAssessmentRun", back_populates="results")
    skill = relationship("Skill")

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="chk_skill_assessment_skill_results_confidence_range",
        ),
        UniqueConstraint("assessment_run_id", "skill_id", name="ux_skill_assessment_skill_results_run_skill"),
        Index("ix_skill_assessment_skill_results_skill_id", "skill_id"),
    )

