from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import DashboardPhase, PhaseStatus, UUIDPrimaryKeyMixin


class DashboardPhaseState(Base, UUIDPrimaryKeyMixin):
    """Per-user per-phase dashboard state.

    Matches `dashboard_phase_state` in the Postgres MVP schema.
    """

    __tablename__ = "dashboard_phase_state"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    phase: Mapped[DashboardPhase] = mapped_column(String(64), nullable=False)
    status: Mapped[PhaseStatus] = mapped_column(String(64), nullable=False, default=PhaseStatus.not_started.value)

    state_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user = relationship("User", back_populates="dashboard_phase_states")

    __table_args__ = (
        UniqueConstraint("user_id", "phase", name="ux_dashboard_phase_state_user_phase"),
        Index("ix_dashboard_phase_state_user_id", "user_id"),
    )

