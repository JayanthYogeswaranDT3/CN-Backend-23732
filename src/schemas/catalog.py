from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


# -------------------------
# Dashboard
# -------------------------


class DashboardUserSummary(BaseModel):
    """Lightweight user info for the dashboard aggregate."""

    id: str = Field(..., description="User id")
    display_name: str = Field(..., description="Display name for greeting")


class DashboardProgress(BaseModel):
    """Overall dashboard progress summary."""

    total_phases: int = Field(..., ge=0, description="Total number of phases")
    completed_phases: int = Field(..., ge=0, description="Number of completed phases")


class DashboardPhaseCTA(BaseModel):
    """Call-to-action metadata for a phase card."""

    label: str = Field(..., description="CTA label")
    route: str = Field(..., description="Frontend route")


class DashboardPhaseCard(BaseModel):
    """Dashboard phase card state."""

    phase: str = Field(..., description="Phase identifier")
    status: str = Field(..., description="Phase status: not_started|in_progress|completed|locked (prototype)")
    cta: DashboardPhaseCTA | None = Field(default=None, description="CTA if phase is actionable")


class DashboardAggregateResponse(BaseModel):
    """Aggregate dashboard payload for rendering the dashboard UI."""

    user: DashboardUserSummary = Field(..., description="User summary")
    progress: DashboardProgress = Field(..., description="Overall progress summary")
    phases: list[DashboardPhaseCard] = Field(default_factory=list, description="Phase cards")


class DashboardPhaseStateRead(BaseModel):
    """Raw phase state row for debugging/hydration."""

    model_config = ConfigDict(from_attributes=True)

    phase: str = Field(..., description="Dashboard phase")
    status: str = Field(..., description="Phase status")
    updated_at: datetime = Field(..., description="Last updated timestamp")
    state_metadata: dict[str, Any] | None = Field(default=None, description="Optional state metadata")


# -------------------------
# Documents
# -------------------------


class DocumentCreate(BaseModel):
    """Create a document metadata record (metadata-first)."""

    doc_type: str = Field(..., description="Document type (resume|certificate|job_description|other)")
    filename: str | None = Field(default=None, description="Original filename")
    content_type: str | None = Field(default=None, description="MIME type")
    storage_key: str | None = Field(default=None, description="Storage key/path in object storage")
    storage_url: str | None = Field(default=None, description="Storage URL (if available)")


class DocumentRead(BaseModel):
    """Document metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Document id")
    doc_type: str = Field(..., description="Document type")
    filename: str | None = Field(default=None, description="Filename")
    content_type: str | None = Field(default=None, description="MIME type")
    storage_key: str | None = Field(default=None, description="Storage key")
    storage_url: str | None = Field(default=None, description="Storage url")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


# -------------------------
# Persona
# -------------------------


class PersonaCreate(BaseModel):
    """Create a persona profile for the current user."""

    summary: str | None = Field(default=None, description="Persona summary")
    attributes: dict[str, Any] | None = Field(default=None, description="Arbitrary persona attributes JSON")


class PersonaRead(BaseModel):
    """Persona profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Persona id")
    summary: str | None = Field(default=None, description="Summary")
    attributes: dict[str, Any] | None = Field(default=None, description="Attributes")
    is_active: bool = Field(..., description="Whether this persona is the active persona")


class PersonaAttachDocumentsRequest(BaseModel):
    """Attach documents to a persona."""

    document_ids: list[str] = Field(default_factory=list, description="Document ids to attach")


class PersonaAttachDocumentsResponse(BaseModel):
    """Response after attaching documents to a persona."""

    persona_id: str = Field(..., description="Persona id")
    document_ids: list[str] = Field(default_factory=list, description="Attached document ids")


class PersonaSkillItem(BaseModel):
    """Persona skill mapping input/output item."""

    skill_id: str = Field(..., description="Skill id")
    level: str | None = Field(default=None, description="Skill level (beginner|intermediate|advanced|expert)")
    confidence: float | None = Field(default=None, ge=0, le=1, description="Confidence 0..1")
    missing_evidence: bool = Field(default=False, description="Whether evidence is missing")


class PersonaSkillsPutRequest(BaseModel):
    """Set persona baseline skills (replace/upsert)."""

    skills: list[PersonaSkillItem] = Field(default_factory=list, description="Skills list")


class PersonaSkillsPutResponse(BaseModel):
    """Response containing persona skill mappings."""

    persona_id: str = Field(..., description="Persona id")
    skills: list[PersonaSkillItem] = Field(default_factory=list, description="Saved skills list")


class ActivePersonaResponse(BaseModel):
    """Active persona convenience response with related ids (prototype-friendly)."""

    persona: PersonaRead = Field(..., description="Active persona profile")
    document_ids: list[str] = Field(default_factory=list, description="Attached document ids")
    skills: list[PersonaSkillItem] = Field(default_factory=list, description="Persona skills")


# -------------------------
# Skills & evidence
# -------------------------


class SkillRead(BaseModel):
    """Canonical skill response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Skill id")
    name: str = Field(..., description="Skill name")
    category: str | None = Field(default=None, description="Skill category")
    description: str | None = Field(default=None, description="Skill description")


class SkillEvidenceCreate(BaseModel):
    """Create evidence record for a skill claim."""

    document_id: str | None = Field(default=None, description="Optional document id used as evidence")
    confidence: float | None = Field(default=None, ge=0, le=1, description="Confidence 0..1")
    evidence_summary: str | None = Field(default=None, description="Short evidence summary")


class SkillEvidenceRead(BaseModel):
    """Skill evidence response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Evidence id")
    skill_id: str = Field(..., description="Skill id")
    document_id: str | None = Field(default=None, description="Document id")
    confidence: float | None = Field(default=None, description="Confidence")
    evidence_summary: str | None = Field(default=None, description="Evidence summary")
    created_at: datetime = Field(..., description="Created timestamp")


# -------------------------
# Questionnaires
# -------------------------


class QuestionnaireTemplateRead(BaseModel):
    """Questionnaire template response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Template id")
    name: str = Field(..., description="Template name")
    version: int = Field(..., description="Template version")
    definition: dict[str, Any] = Field(..., description="Template definition JSON")
    is_active: bool = Field(..., description="Whether template is active")


class QuestionnaireResponseCreate(BaseModel):
    """Submit questionnaire response."""

    template_id: str | None = Field(default=None, description="Template id (optional)")
    answers: dict[str, Any] = Field(..., description="Answers JSON")
    total_score: float | None = Field(default=None, description="Optional total score")


class QuestionnaireResponseRead(BaseModel):
    """Questionnaire response read."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Response id")
    template_id: str | None = Field(default=None, description="Template id")
    completed_at: datetime = Field(..., description="Completion timestamp")
    total_score: float | None = Field(default=None, description="Total score")


# -------------------------
# Assessments
# -------------------------


class AssessmentCreate(BaseModel):
    """Create an assessment run."""

    persona_id: str | None = Field(default=None, description="Persona id used for assessment")
    questionnaire_response_id: str | None = Field(default=None, description="Questionnaire response id")


class AssessmentRunRead(BaseModel):
    """Assessment run response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Assessment run id")
    status: str = Field(..., description="Status")
    started_at: datetime = Field(..., description="Started at")
    completed_at: datetime | None = Field(default=None, description="Completed at")


class AssessmentResultItem(BaseModel):
    """Per-skill assessment result."""

    skill_id: str = Field(..., description="Skill id")
    final_level: str | None = Field(default=None, description="Final level")
    confidence: float | None = Field(default=None, ge=0, le=1, description="Confidence 0..1")
    missing_evidence: bool = Field(default=False, description="Missing evidence flag")
    notes: str | None = Field(default=None, description="Optional notes")


class AssessmentResultsPutRequest(BaseModel):
    """Upsert assessment results (per skill)."""

    results: list[AssessmentResultItem] = Field(default_factory=list, description="Results list")


class AssessmentResultsResponse(BaseModel):
    """Assessment results response."""

    assessment_id: str = Field(..., description="Assessment run id")
    results: list[AssessmentResultItem] = Field(default_factory=list, description="Results list")


class LatestAssessmentResponse(BaseModel):
    """Latest assessment + results."""

    assessment: AssessmentRunRead = Field(..., description="Latest assessment run")
    results: list[AssessmentResultItem] = Field(default_factory=list, description="Associated results")


# -------------------------
# Career paths
# -------------------------


class CareerPathRead(BaseModel):
    """Career path list/detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Career path id")
    name: str = Field(..., description="Name")
    summary: str | None = Field(default=None, description="Summary")
    is_active: bool = Field(..., description="Active flag")


class CareerPathSkillRead(BaseModel):
    """Career path skill requirement."""

    skill_id: str = Field(..., description="Skill id")
    target_level: str | None = Field(default=None, description="Target level")
    is_required: bool = Field(default=True, description="Required flag")
    weight: float | None = Field(default=None, description="Optional weight")


class CareerPathDetailResponse(CareerPathRead):
    """Career path detail including skills."""

    skills: list[CareerPathSkillRead] = Field(default_factory=list, description="Skill requirements/targets")


class CareerPathRecommendationRead(BaseModel):
    """Recommendation response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Recommendation id")
    career_path_id: str = Field(..., description="Career path id")
    fit_score: float | None = Field(default=None, description="Fit score")
    explanation: str | None = Field(default=None, description="Explanation")
    created_at: datetime = Field(..., description="Created at")


class CareerPathSelectionCreate(BaseModel):
    """Select a career path."""

    career_path_id: str = Field(..., description="Career path id to select")


class CareerPathSelectionRead(BaseModel):
    """Selection response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Selection id")
    career_path_id: str = Field(..., description="Career path id")
    is_active: bool = Field(..., description="Active flag")
    selected_at: datetime = Field(..., description="Selected at")


# -------------------------
# Roadmaps
# -------------------------


class RoadmapCreate(BaseModel):
    """Create/regenerate roadmap."""

    career_path_id: str = Field(..., description="Career path id")
    title: str | None = Field(default=None, description="Optional title")
    description: str | None = Field(default=None, description="Optional description")


class MilestoneTaskRead(BaseModel):
    """Milestone task response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Task id")
    title: str = Field(..., description="Title")
    description: str | None = Field(default=None, description="Description")
    is_complete: bool = Field(..., description="Completion flag")


class MilestoneRead(BaseModel):
    """Milestone response including tasks."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Milestone id")
    title: str = Field(..., description="Title")
    description: str | None = Field(default=None, description="Description")
    is_complete: bool = Field(..., description="Completion flag")
    tasks: list[MilestoneTaskRead] = Field(default_factory=list, description="Tasks")


class RoadmapRead(BaseModel):
    """Roadmap response including milestones and tasks."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Roadmap id")
    title: str | None = Field(default=None, description="Title")
    description: str | None = Field(default=None, description="Description")
    status: str = Field(..., description="Status")
    career_path_id: str | None = Field(default=None, description="Career path id")
    milestones: list[MilestoneRead] = Field(default_factory=list, description="Milestones")


class PatchCompletionRequest(BaseModel):
    """Patch completion flag."""

    is_complete: bool = Field(..., description="New completion value")


# -------------------------
# Marketplace
# -------------------------


class MarketplaceItemRead(BaseModel):
    """Marketplace item response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Marketplace item id")
    title: str = Field(..., description="Title")
    item_type: str = Field(..., description="Type (course|certification|job|...)")
    url: str | None = Field(default=None, description="URL")
    short_desc: str | None = Field(default=None, description="Short description")


class RoadmapMarketplaceItemRead(MarketplaceItemRead):
    """Marketplace item linked to roadmap with relevance fields."""

    relevance_score: float | None = Field(default=None, description="Relevance score")
    note: str | None = Field(default=None, description="Optional note")


class MarketplaceListResponse(BaseModel):
    """List response for roadmap/milestone marketplace linkage endpoints."""

    items: list[RoadmapMarketplaceItemRead] = Field(default_factory=list, description="Items")
