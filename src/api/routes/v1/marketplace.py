from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.marketplace import MarketplaceItem
from src.models.user import User
from src.schemas.catalog import MarketplaceItemRead
from src.schemas.common import Paginated

router = APIRouter()


@router.get(
    "/items",
    response_model=Paginated[MarketplaceItemRead],
    status_code=status.HTTP_200_OK,
    summary="List marketplace items",
    description="Browse/search curated marketplace catalog.",
    operation_id="marketplace_list_items",
)
async def list_marketplace_items(
    item_type: str | None = Query(default=None, description="Optional item type filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Paginated[MarketplaceItemRead]:
    """List marketplace items with optional type filter."""
    where = [MarketplaceItem.is_active.is_(True)]
    if item_type:
        where.append(MarketplaceItem.item_type == item_type)

    items_stmt = select(MarketplaceItem).where(*where).order_by(MarketplaceItem.created_at.desc()).limit(limit).offset(offset)
    total_stmt = select(func.count()).select_from(MarketplaceItem).where(*where)

    items_res = await db.execute(items_stmt)
    total_res = await db.execute(total_stmt)

    items = [MarketplaceItemRead.model_validate(x) for x in items_res.scalars().all()]
    total = int(total_res.scalar_one())
    return Paginated[MarketplaceItemRead](items=items, total=total, limit=limit, offset=offset)
