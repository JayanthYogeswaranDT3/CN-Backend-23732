from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import SkillLevel, TimestampAuditMixin, UUIDPrimaryKeyMixin


class Skill(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Canonical skill taxonomy entity.

    Matches `skills` in the Postgres MVP schema.
    """

    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    taxonomy_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    persona_mappings = relationship("PersonaSkillMap", back_populates="skill")
    evidence = relationship("SkillEvidence", back_populates="skill")
    career_path_links = relationship("CareerPathSkill", back_populates="skill")


class SkillEvidence(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Evidence supporting a user's skill claim.

    Matches `skill_evidence` in the Postgres MVP schema.
    """

    __tablename__ = "skill_evidence"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("document_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user = relationship("User", foreign_keys=[user_id], back_populates="skill_evidence")
    skill = relationship("Skill", back_populates="evidence")
    document = relationship("DocumentSource", back_populates="skill_evidence")

    __table_args__ = (
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="chk_skill_evidence_confidence_range"),
        # Mirrors partial unique index in schema (only when document_id IS NOT NULL).
        # In ORM we model as a normal uniqueness constraint; DB migrations should ideally
        # implement the partial index for exact parity.
        UniqueConstraint("user_id", "skill_id", "document_id", name="ux_skill_evidence_user_skill_document"),
        Index("ix_skill_evidence_user_skill", "user_id", "skill_id"),
    )


class PersonaSkillMap(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Mapping between persona profile and canonical skills.

    Matches `persona_skill_map` in the Postgres MVP schema.
    """

    __tablename__ = "persona_skill_map"

    persona_id: Mapped[str] = mapped_column(
        ForeignKey("persona_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    level: Mapped[Optional[SkillLevel]] = mapped_column(String(32), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    missing_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    persona = relationship("PersonaProfile", back_populates="skills")
    skill = relationship("Skill", back_populates="persona_mappings")

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="chk_persona_skill_map_confidence_range",
        ),
        UniqueConstraint("persona_id", "skill_id", name="ux_persona_skill_map_persona_skill"),
    )

