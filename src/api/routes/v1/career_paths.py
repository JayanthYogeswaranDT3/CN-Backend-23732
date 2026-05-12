from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select, update

from src.api.errors.exceptions import NotFoundError
from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.career_path import CareerPath, CareerPathRecommendation, CareerPathSkill, UserCareerPathSelection
from src.models.user import User
from src.schemas.catalog import (
    CareerPathDetailResponse,
    CareerPathRead,
    CareerPathRecommendationRead,
    CareerPathSelectionCreate,
    CareerPathSelectionRead,
    CareerPathSkillRead,
)
from src.schemas.common import Paginated

router = APIRouter()


@router.get(
    "",
    response_model=Paginated[CareerPathRead],
    status_code=status.HTTP_200_OK,
    summary="List career paths",
    description="Browse available career paths.",
    operation_id="career_paths_list",
)
async def list_career_paths(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Paginated[CareerPathRead]:
    """List active career paths."""
    items_stmt = (
        select(CareerPath)
        .where(CareerPath.is_active.is_(True))
        .order_by(CareerPath.name.asc())
        .limit(limit)
        .offset(offset)
    )
    total_stmt = select(func.count()).select_from(CareerPath).where(CareerPath.is_active.is_(True))

    items_res = await db.execute(items_stmt)
    total_res = await db.execute(total_stmt)

    items = [CareerPathRead.model_validate(x) for x in items_res.scalars().all()]
    total = int(total_res.scalar_one())
    return Paginated[CareerPathRead](items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{career_path_id}",
    response_model=CareerPathDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get career path detail",
    description="Returns a career path including its skill requirements/targets.",
    operation_id="career_paths_get",
)
async def get_career_path(
    career_path_id: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CareerPathDetailResponse:
    """Get career path detail."""
    cp = await db.get(CareerPath, career_path_id)
    if cp is None or not cp.is_active:
        raise NotFoundError("Career path not found")

    skills_res = await db.execute(select(CareerPathSkill).where(CareerPathSkill.career_path_id == career_path_id))
    skills = [
        CareerPathSkillRead(
            skill_id=s.skill_id,
            target_level=str(s.target_level) if s.target_level is not None else None,
            is_required=bool(s.is_required),
            weight=float(s.weight) if s.weight is not None else None,
        )
        for s in skills_res.scalars().all()
    ]

    base = CareerPathRead.model_validate(cp).model_dump()
    return CareerPathDetailResponse(**base, skills=skills)


@router.get(
    "/recommendations",
    response_model=Paginated[CareerPathRecommendationRead],
    status_code=status.HTTP_200_OK,
    summary="List career path recommendations",
    description="Returns recommendations for the authenticated user.",
    operation_id="career_path_recommendations_list",
)
async def list_recommendations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Paginated[CareerPathRecommendationRead]:
    """List recommendations for the current user."""
    items_stmt = (
        select(CareerPathRecommendation)
        .where(CareerPathRecommendation.user_id == current_user.id)
        .order_by(CareerPathRecommendation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    total_stmt = (
        select(func.count())
        .select_from(CareerPathRecommendation)
        .where(CareerPathRecommendation.user_id == current_user.id)
    )

    items_res = await db.execute(items_stmt)
    total_res = await db.execute(total_stmt)

    items = [CareerPathRecommendationRead.model_validate(x) for x in items_res.scalars().all()]
    total = int(total_res.scalar_one())
    return Paginated[CareerPathRecommendationRead](items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/selections",
    response_model=CareerPathSelectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Select a career path",
    description="Stores the user's selected target path (one active selection).",
    operation_id="career_path_selections_create",
)
async def select_career_path(
    payload: CareerPathSelectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CareerPathSelectionRead:
    """Select a career path for the current user."""
    cp = await db.get(CareerPath, payload.career_path_id)
    if cp is None or not cp.is_active:
        raise NotFoundError("Career path not found")

    # Deactivate existing selections
    await db.execute(
        update(UserCareerPathSelection)
        .where(UserCareerPathSelection.user_id == current_user.id)
        .where(UserCareerPathSelection.is_active.is_(True))
        .values(is_active=False, updated_at=datetime.now(timezone.utc))
    )

    now = datetime.now(timezone.utc)
    selection = UserCareerPathSelection(
        user_id=current_user.id,
        career_path_id=payload.career_path_id,
        is_active=True,
        selected_at=now,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(selection)
    await db.flush()
    return CareerPathSelectionRead.model_validate(selection)
