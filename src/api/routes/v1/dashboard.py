from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select

from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.dashboard import DashboardPhaseState
from src.models.user import User
from src.schemas.catalog import (
    DashboardAggregateResponse,
    DashboardPhaseCard,
    DashboardPhaseCTA,
    DashboardPhaseStateRead,
    DashboardProgress,
    DashboardUserSummary,
)

router = APIRouter()

# Prototype phase ordering (matches the endpoint catalog narrative)
_PHASES: list[str] = ["build_profile", "skill_assessment", "career_path", "roadmap", "marketplace"]


@router.get(
    "",
    response_model=DashboardAggregateResponse,
    status_code=status.HTTP_200_OK,
    summary="Dashboard aggregate",
    description="Single aggregate payload used by the frontend dashboard.",
    operation_id="dashboard_get_aggregate",
)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DashboardAggregateResponse:
    """Return a dashboard aggregate response for the current user."""
    stmt = select(DashboardPhaseState).where(DashboardPhaseState.user_id == current_user.id)
    res = await db.execute(stmt)
    states = {row.phase: row for row in res.scalars().all()}

    def _status_for_phase(phase: str) -> str:
        if phase in states:
            return str(states[phase].status)
        return "not_started"

    # Determine locking: phases after first incomplete are locked (prototype rule)
    completed_count = 0
    first_incomplete_idx = None
    for idx, phase in enumerate(_PHASES):
        st = _status_for_phase(phase)
        if st == "completed":
            completed_count += 1
        else:
            first_incomplete_idx = idx
            break

    cards: list[DashboardPhaseCard] = []
    for idx, phase in enumerate(_PHASES):
        st = _status_for_phase(phase)
        if first_incomplete_idx is not None and idx > first_incomplete_idx and st != "completed":
            st = "locked"

        cta = None
        if st in {"not_started", "in_progress", "completed"}:
            # Keep routes aligned to the endpoint catalog examples (frontend can ignore/override).
            route_map = {
                "build_profile": "/build-profile",
                "skill_assessment": "/skill-assessment",
                "career_path": "/career-paths",
                "roadmap": "/roadmap",
                "marketplace": "/marketplace",
            }
            cta = DashboardPhaseCTA(label="Continue", route=route_map.get(phase, "/"))

        cards.append(DashboardPhaseCard(phase=phase, status=st, cta=cta))

    return DashboardAggregateResponse(
        user=DashboardUserSummary(id=current_user.id, display_name=current_user.full_name or current_user.email),
        progress=DashboardProgress(total_phases=len(_PHASES), completed_phases=completed_count),
        phases=cards,
    )


@router.get(
    "/phases",
    response_model=list[DashboardPhaseStateRead],
    status_code=status.HTTP_200_OK,
    summary="List dashboard phase states",
    description="Returns raw dashboard phase state records for the current user.",
    operation_id="dashboard_list_phases",
)
async def list_dashboard_phases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DashboardPhaseStateRead]:
    """List phase state records for the authenticated user."""
    stmt = (
        select(DashboardPhaseState)
        .where(DashboardPhaseState.user_id == current_user.id)
        .order_by(DashboardPhaseState.updated_at.desc())
    )
    res = await db.execute(stmt)
    return [DashboardPhaseStateRead.model_validate(x) for x in res.scalars().all()]
