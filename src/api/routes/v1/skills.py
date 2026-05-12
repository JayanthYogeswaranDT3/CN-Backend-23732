from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

from src.api.errors.exceptions import NotFoundError
from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.document import DocumentSource
from src.models.skill import Skill, SkillEvidence
from src.models.user import User
from src.schemas.catalog import SkillEvidenceCreate, SkillEvidenceRead, SkillRead
from src.schemas.common import Paginated

router = APIRouter()


@router.get(
    "",
    response_model=Paginated[SkillRead],
    status_code=status.HTTP_200_OK,
    summary="List/search skills",
    description="Search/browse canonical skills taxonomy.",
    operation_id="skills_list",
)
async def list_skills(
    query: str | None = Query(default=None, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Paginated[SkillRead]:
    """List skills, optionally filtering by query on name (case-insensitive)."""
    where = []
    if query:
        where.append(Skill.name.ilike(f"%{query}%"))

    items_stmt = select(Skill).where(*where).order_by(Skill.name.asc()).limit(limit).offset(offset)
    total_stmt = select(func.count()).select_from(Skill).where(*where)

    items_res = await db.execute(items_stmt)
    total_res = await db.execute(total_stmt)

    items = [SkillRead.model_validate(x) for x in items_res.scalars().all()]
    total = int(total_res.scalar_one())
    return Paginated[SkillRead](items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/{skill_id}/evidence",
    response_model=SkillEvidenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add skill evidence",
    description="Attach evidence (usually a document) to support a skill claim for the current user.",
    operation_id="skills_create_evidence",
)
async def add_skill_evidence(
    skill_id: str,
    payload: SkillEvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SkillEvidenceRead:
    """Create a skill evidence record for the authenticated user."""
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise NotFoundError("Skill not found")

    if payload.document_id:
        doc = await db.get(DocumentSource, payload.document_id)
        if doc is None or doc.user_id != current_user.id or doc.deleted_at is not None:
            raise NotFoundError("Document not found")

    now = datetime.now(timezone.utc)
    ev = SkillEvidence(
        user_id=current_user.id,
        skill_id=skill_id,
        document_id=payload.document_id,
        confidence=payload.confidence,
        evidence_summary=payload.evidence_summary,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(ev)
    await db.flush()
    return SkillEvidenceRead.model_validate(ev)


@router.get(
    "/evidence",
    response_model=Paginated[SkillEvidenceRead],
    status_code=status.HTTP_200_OK,
    summary="List my skill evidence",
    description="Lists skill evidence records belonging to the authenticated user.",
    operation_id="skills_list_my_evidence",
)
async def list_my_skill_evidence(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Paginated[SkillEvidenceRead]:
    """List the current user's skill evidence with pagination."""
    items_stmt = (
        select(SkillEvidence)
        .where(SkillEvidence.user_id == current_user.id)
        .order_by(SkillEvidence.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    total_stmt = select(func.count()).select_from(SkillEvidence).where(SkillEvidence.user_id == current_user.id)

    items_res = await db.execute(items_stmt)
    total_res = await db.execute(total_stmt)

    items = [SkillEvidenceRead.model_validate(x) for x in items_res.scalars().all()]
    total = int(total_res.scalar_one())
    return Paginated[SkillEvidenceRead](items=items, total=total, limit=limit, offset=offset)
