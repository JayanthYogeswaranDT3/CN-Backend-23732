from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from src.api.errors.exceptions import NotFoundError
from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.assessment import SkillAssessmentRun, SkillAssessmentSkillResult
from src.models.persona import PersonaProfile
from src.models.questionnaire import QuestionnaireResponse
from src.models.skill import Skill
from src.models.user import User
from src.schemas.catalog import (
    AssessmentCreate,
    AssessmentResultsPutRequest,
    AssessmentResultsResponse,
    AssessmentRunRead,
    LatestAssessmentResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=AssessmentRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create skill assessment run",
    description="Creates an assessment run binding persona and questionnaire response (prototype).",
    operation_id="assessments_create",
)
async def create_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AssessmentRunRead:
    """Create an assessment run for the current user."""
    if payload.persona_id:
        persona = await db.get(PersonaProfile, payload.persona_id)
        if persona is None or persona.user_id != current_user.id or persona.deleted_at is not None:
            raise NotFoundError("Persona not found")

    if payload.questionnaire_response_id:
        qr = await db.get(QuestionnaireResponse, payload.questionnaire_response_id)
        if qr is None or qr.user_id != current_user.id:
            raise NotFoundError("Questionnaire response not found")

    now = datetime.now(timezone.utc)
    run = SkillAssessmentRun(
        user_id=current_user.id,
        persona_id=payload.persona_id,
        questionnaire_response_id=payload.questionnaire_response_id,
        status="completed",
        started_at=now,
        completed_at=now,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(run)
    await db.flush()
    return AssessmentRunRead.model_validate(run)


@router.put(
    "/{assessment_id}/results",
    response_model=AssessmentResultsResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert assessment results",
    description="Upserts per-skill final level/confidence/missing_evidence (prototype-friendly).",
    operation_id="assessments_put_results",
)
async def put_results(
    assessment_id: str,
    payload: AssessmentResultsPutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AssessmentResultsResponse:
    """Upsert assessment results for an assessment run belonging to the current user."""
    run = await db.get(SkillAssessmentRun, assessment_id)
    if run is None or run.user_id != current_user.id:
        raise NotFoundError("Assessment not found")

    # Load existing results for upsert
    existing_res = await db.execute(
        select(SkillAssessmentSkillResult).where(SkillAssessmentSkillResult.assessment_run_id == assessment_id)
    )
    existing = {r.skill_id: r for r in existing_res.scalars().all()}

    now = datetime.now(timezone.utc)
    for item in payload.results:
        # Validate skill exists
        skill = await db.get(Skill, item.skill_id)
        if skill is None:
            raise NotFoundError(f"Skill not found: {item.skill_id}")

        row = existing.get(item.skill_id)
        if row is None:
            row = SkillAssessmentSkillResult(
                assessment_run_id=assessment_id,
                skill_id=item.skill_id,
                created_at=now,
                updated_at=now,
            )
            db.add(row)
        row.final_level = item.final_level
        row.confidence = item.confidence
        row.missing_evidence = item.missing_evidence
        row.notes = item.notes
        row.updated_at = now

    await db.flush()
    return AssessmentResultsResponse(assessment_id=assessment_id, results=payload.results)


@router.get(
    "/latest",
    response_model=LatestAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest assessment",
    description="Returns the most recent assessment run and its results for the current user.",
    operation_id="assessments_get_latest",
)
async def get_latest_assessment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LatestAssessmentResponse:
    """Get latest assessment run + results."""
    run_res = await db.execute(
        select(SkillAssessmentRun)
        .where(SkillAssessmentRun.user_id == current_user.id)
        .order_by(SkillAssessmentRun.started_at.desc())
        .limit(1)
    )
    run = run_res.scalar_one_or_none()
    if run is None:
        raise NotFoundError("No assessments found")

    results_res = await db.execute(
        select(SkillAssessmentSkillResult).where(SkillAssessmentSkillResult.assessment_run_id == run.id)
    )
    results = [
        {
            "skill_id": r.skill_id,
            "final_level": str(r.final_level) if r.final_level is not None else None,
            "confidence": float(r.confidence) if r.confidence is not None else None,
            "missing_evidence": bool(r.missing_evidence),
            "notes": r.notes,
        }
        for r in results_res.scalars().all()
    ]

    return LatestAssessmentResponse(
        assessment=AssessmentRunRead.model_validate(run),
        results=results,  # Pydantic will validate list[AssessmentResultItem]-compatible dicts
    )
