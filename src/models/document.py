from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import CreatedByMixin, DocumentType, SoftDeleteMixin, TimestampAuditMixin, UUIDPrimaryKeyMixin


class DocumentSource(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin, CreatedByMixin, SoftDeleteMixin):
    """User-owned document metadata and optional extracted content.

    Matches `document_sources` in the Postgres MVP schema. The actual file bytes
    are expected to be stored in object storage; this table stores pointers.
    """

    __tablename__ = "document_sources"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    doc_type: Mapped[DocumentType] = mapped_column(String(32), nullable=False, index=True)

    filename: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    personas = relationship("PersonaDocument", back_populates="document", cascade="all, delete-orphan")
    skill_evidence = relationship("SkillEvidence", back_populates="document")


Index("ix_document_sources_user_id", DocumentSource.user_id)
Index("ix_document_sources_doc_type", DocumentSource.doc_type)

