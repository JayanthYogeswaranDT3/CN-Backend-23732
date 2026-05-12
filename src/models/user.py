from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.time import utcnow
from src.db.base import Base


class User(Base):
    """User ORM model (sample entity)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Note: existing scaffold stores created_at as ISO string.
    # New models use timestamptz-like DateTime; user model left unchanged to avoid
    # breaking existing APIs/tests in this subtask.
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=lambda: utcnow().isoformat())

    # Relationships (defined by string to avoid import cycles)
    persona_profiles = relationship("PersonaProfile", back_populates="user")
    documents = relationship("DocumentSource", back_populates="user")
    questionnaire_responses = relationship("QuestionnaireResponse", back_populates="user")
    skill_assessment_runs = relationship("SkillAssessmentRun", back_populates="user")
    career_path_recommendations = relationship("CareerPathRecommendation", back_populates="user")
    career_path_selections = relationship("UserCareerPathSelection", back_populates="user")
    roadmaps = relationship("Roadmap", back_populates="user")
    dashboard_phase_states = relationship("DashboardPhaseState", back_populates="user")
    skill_evidence = relationship("SkillEvidence", back_populates="user")

