from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import TimestampAuditMixin, UUIDPrimaryKeyMixin


class QuestionnaireTemplate(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Versioned questionnaire definition stored as JSON.

    Matches `questionnaire_templates` in the Postgres MVP schema.
    """

    __tablename__ = "questionnaire_templates"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    definition: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    responses = relationship("QuestionnaireResponse", back_populates="template")

    __table_args__ = (
        UniqueConstraint("name", "version", name="ux_questionnaire_templates_name_version"),
        Index("ix_questionnaire_templates_is_active", "is_active"),
    )


class QuestionnaireResponse(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """A user's questionnaire submission.

    Matches `questionnaire_responses` in the Postgres MVP schema.
    """

    __tablename__ = "questionnaire_responses"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("questionnaire_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    total_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)

    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user = relationship("User", back_populates="questionnaire_responses")
    template = relationship("QuestionnaireTemplate", back_populates="responses")
    assessment_runs = relationship("SkillAssessmentRun", back_populates="questionnaire_response")

