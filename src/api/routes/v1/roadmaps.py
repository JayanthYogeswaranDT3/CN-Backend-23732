from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from src.api.errors.exceptions import NotFoundError
from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.marketplace import MarketplaceItem, MilestoneMarketplaceItem, RoadmapMarketplaceItem
from src.models.roadmap import Milestone, MilestoneTask, Roadmap
from src.models.user import User
from src.schemas.catalog import (
    MarketplaceListResponse,
    PatchCompletionRequest,
    RoadmapCreate,
    RoadmapMarketplaceItemRead,
    RoadmapRead,
)

router = APIRouter()


def _roadmap_to_read(roadmap: Roadmap) -> RoadmapRead:
    """Convert a Roadmap ORM object to RoadmapRead using loaded relationships."""
    milestones = []
    for m in getattr(roadmap, "milestones", []) or []:
        tasks = []
        for t in getattr(m, "tasks", []) or []:
            tasks.append(
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "is_complete": bool(t.is_complete),
                }
            )
        milestones.append(
            {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "is_complete": bool(m.is_complete),
                "tasks": tasks,
            }
        )

    return RoadmapRead(
        id=roadmap.id,
        title=roadmap.title,
        description=roadmap.description,
        status=roadmap.status,
        career_path_id=roadmap.career_path_id,
        milestones=milestones,
    )


@router.get(
    "/active",
    response_model=RoadmapRead,
    status_code=status.HTTP_200_OK,
    summary="Get active roadmap",
    description="Returns the current user's active roadmap including milestones and tasks.",
    operation_id="roadmaps_get_active",
)
async def get_active_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RoadmapRead:
    """Fetch the latest active roadmap for the current user."""
    res = await db.execute(
        select(Roadmap)
        .where(Roadmap.user_id == current_user.id)
        .where(Roadmap.status == "active")
        .where(Roadmap.deleted_at.is_(None))
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    roadmap = res.scalar_one_or_none()
    if roadmap is None:
        raise NotFoundError("Active roadmap not found")

    # Load milestones + tasks (simple explicit loads; avoids relying on lazy loading in async contexts)
    milestones_res = await db.execute(select(Milestone).where(Milestone.roadmap_id == roadmap.id).order_by(Milestone.sort_order.asc()))
    milestones = milestones_res.scalars().all()
    for m in milestones:
        tasks_res = await db.execute(select(MilestoneTask).where(MilestoneTask.milestone_id == m.id).order_by(MilestoneTask.sort_order.asc()))
        m.tasks = list(tasks_res.scalars().all())  # type: ignore[attr-defined]
    roadmap.milestones = list(milestones)  # type: ignore[attr-defined]

    return _roadmap_to_read(roadmap)


@router.post(
    "",
    response_model=RoadmapRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create roadmap",
    description="Creates a new active roadmap for the current user (prototype).",
    operation_id="roadmaps_create",
)
async def create_roadmap(
    payload: RoadmapCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RoadmapRead:
    """Create a roadmap (prototype; no milestone generation included)."""
    now = datetime.now(timezone.utc)
    roadmap = Roadmap(
        user_id=current_user.id,
        career_path_id=payload.career_path_id,
        title=payload.title,
        description=payload.description,
        status="active",
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(roadmap)
    await db.flush()
    roadmap.milestones = []  # type: ignore[attr-defined]
    return _roadmap_to_read(roadmap)


@router.patch(
    "/milestones/{milestone_id}",
    status_code=status.HTTP_200_OK,
    summary="Patch milestone completion",
    description="Updates milestone completion fields for a milestone belonging to the current user.",
    operation_id="milestones_patch",
)
async def patch_milestone(
    milestone_id: str,
    payload: PatchCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Patch milestone completion."""
    milestone = await db.get(Milestone, milestone_id)
    if milestone is None:
        raise NotFoundError("Milestone not found")

    roadmap = await db.get(Roadmap, milestone.roadmap_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise NotFoundError("Milestone not found")

    milestone.is_complete = payload.is_complete
    milestone.completed_at = datetime.now(timezone.utc) if payload.is_complete else None
    milestone.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"id": milestone.id, "is_complete": bool(milestone.is_complete)}


@router.patch(
    "/milestone-tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Patch task completion",
    description="Updates milestone task completion fields for a task belonging to the current user.",
    operation_id="milestone_tasks_patch",
)
async def patch_task(
    task_id: str,
    payload: PatchCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Patch milestone task completion."""
    task = await db.get(MilestoneTask, task_id)
    if task is None:
        raise NotFoundError("Task not found")

    milestone = await db.get(Milestone, task.milestone_id)
    if milestone is None:
        raise NotFoundError("Task not found")

    roadmap = await db.get(Roadmap, milestone.roadmap_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise NotFoundError("Task not found")

    task.is_complete = payload.is_complete
    task.completed_at = datetime.now(timezone.utc) if payload.is_complete else None
    task.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"id": task.id, "is_complete": bool(task.is_complete)}


@router.get(
    "/active/marketplace-items",
    response_model=MarketplaceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get marketplace items for active roadmap",
    description="Returns items linked to the active roadmap.",
    operation_id="roadmaps_get_active_marketplace_items",
)
async def get_active_roadmap_marketplace_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MarketplaceListResponse:
    """Return marketplace items linked to the current user's active roadmap."""
    res = await db.execute(
        select(Roadmap)
        .where(Roadmap.user_id == current_user.id)
        .where(Roadmap.status == "active")
        .where(Roadmap.deleted_at.is_(None))
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    roadmap = res.scalar_one_or_none()
    if roadmap is None:
        raise NotFoundError("Active roadmap not found")

    links_res = await db.execute(select(RoadmapMarketplaceItem).where(RoadmapMarketplaceItem.roadmap_id == roadmap.id))
    links = links_res.scalars().all()
    if not links:
        return MarketplaceListResponse(items=[])

    item_ids = [l.marketplace_item_id for l in links]
    items_res = await db.execute(select(MarketplaceItem).where(MarketplaceItem.id.in_(item_ids)))  # type: ignore[arg-type]
    items_map = {i.id: i for i in items_res.scalars().all()}

    out = []
    for link in links:
        item = items_map.get(link.marketplace_item_id)
        if not item:
            continue
        out.append(
            RoadmapMarketplaceItemRead(
                id=item.id,
                title=item.title,
                item_type=str(item.item_type),
                url=item.url,
                short_desc=item.short_desc,
                relevance_score=float(link.relevance_score) if link.relevance_score is not None else None,
                note=link.note,
            )
        )
    return MarketplaceListResponse(items=out)


@router.get(
    "/milestones/{milestone_id}/marketplace-items",
    response_model=MarketplaceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get marketplace items for milestone",
    description="Returns items linked to a milestone belonging to the current user.",
    operation_id="milestones_get_marketplace_items",
)
async def get_milestone_marketplace_items(
    milestone_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MarketplaceListResponse:
    """Return marketplace items linked to a milestone (ownership enforced via roadmap)."""
    milestone = await db.get(Milestone, milestone_id)
    if milestone is None:
        raise NotFoundError("Milestone not found")

    roadmap = await db.get(Roadmap, milestone.roadmap_id)
    if roadmap is None or roadmap.user_id != current_user.id:
        raise NotFoundError("Milestone not found")

    links_res = await db.execute(select(MilestoneMarketplaceItem).where(MilestoneMarketplaceItem.milestone_id == milestone_id))
    links = links_res.scalars().all()
    if not links:
        return MarketplaceListResponse(items=[])

    item_ids = [l.marketplace_item_id for l in links]
    items_res = await db.execute(select(MarketplaceItem).where(MarketplaceItem.id.in_(item_ids)))  # type: ignore[arg-type]
    items_map = {i.id: i for i in items_res.scalars().all()}

    out = []
    for link in links:
        item = items_map.get(link.marketplace_item_id)
        if not item:
            continue
        out.append(
            RoadmapMarketplaceItemRead(
                id=item.id,
                title=item.title,
                item_type=str(item.item_type),
                url=item.url,
                short_desc=item.short_desc,
                relevance_score=float(link.relevance_score) if link.relevance_score is not None else None,
                note=link.note,
            )
        )
    return MarketplaceListResponse(items=out)
