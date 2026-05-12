from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from src.api.errors.exceptions import NotFoundError
from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.questionnaire import QuestionnaireResponse, QuestionnaireTemplate
from src.models.user import User
from src.schemas.catalog import (
    QuestionnaireResponseCreate,
    QuestionnaireResponseRead,
    QuestionnaireTemplateRead,
)

router = APIRouter()


@router.get(
    "/active",
    response_model=QuestionnaireTemplateRead,
    status_code=status.HTTP_200_OK,
    summary="Get active questionnaire template",
    description="Returns the currently active questionnaire definition.",
    operation_id="questionnaires_get_active",
)
async def get_active_template(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> QuestionnaireTemplateRead:
    """Get the active questionnaire template."""
    res = await db.execute(
        select(QuestionnaireTemplate).where(QuestionnaireTemplate.is_active.is_(True)).order_by(QuestionnaireTemplate.created_at.desc()).limit(1)
    )
    template = res.scalar_one_or_none()
    if template is None:
        raise NotFoundError("No active questionnaire template")
    return QuestionnaireTemplateRead.model_validate(template)


@router.post(
    "/responses",
    response_model=QuestionnaireResponseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit questionnaire response",
    description="Persists questionnaire answers for the authenticated user.",
    operation_id="questionnaire_responses_create",
)
async def submit_response(
    payload: QuestionnaireResponseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> QuestionnaireResponseRead:
    """Create a questionnaire response."""
    if payload.template_id:
        tmpl = await db.get(QuestionnaireTemplate, payload.template_id)
        if tmpl is None:
            raise NotFoundError("Template not found")

    now = datetime.now(timezone.utc)
    resp = QuestionnaireResponse(
        user_id=current_user.id,
        template_id=payload.template_id,
        answers=payload.answers,
        total_score=payload.total_score,
        completed_at=now,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(resp)
    await db.flush()
    return QuestionnaireResponseRead.model_validate(resp)
