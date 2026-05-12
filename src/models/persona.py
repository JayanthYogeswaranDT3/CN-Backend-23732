from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import CreatedByMixin, SoftDeleteMixin, TimestampAuditMixin, UUIDPrimaryKeyMixin


class PersonaProfile(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin, CreatedByMixin, SoftDeleteMixin):
    """Persona profile snapshot for a user.

    Matches `persona_profiles` in the Postgres MVP schema. A user may have multiple
    persona profiles (versioned over time). The schema intends "one active persona
    per user" via a partial unique index; that constraint should be enforced via
    migrations/DDL (not represented directly in SQLAlchemy).
    """

    __tablename__ = "persona_profiles"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    user = relationship("User", back_populates="persona_profiles")
    documents = relationship("PersonaDocument", back_populates="persona", cascade="all, delete-orphan")
    skills = relationship("PersonaSkillMap", back_populates="persona", cascade="all, delete-orphan")


class PersonaDocument(Base):
    """Junction table linking persona profiles to document sources.

    Matches `persona_documents` in the Postgres MVP schema.
    Composite primary key: (persona_id, document_id)
    """

    __tablename__ = "persona_documents"

    persona_id: Mapped[str] = mapped_column(
        ForeignKey("persona_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("document_sources.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    persona = relationship("PersonaProfile", back_populates="documents")
    document = relationship("DocumentSource", back_populates="personas")


Index("ix_persona_documents_document_id", PersonaDocument.document_id)

