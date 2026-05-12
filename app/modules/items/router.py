from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, http_404
from app.db.session import get_db_session
from app.modules.items.schemas import ItemCreate, ItemRead, ItemUpdate
from app.modules.items.service import ItemService

router = APIRouter()


def get_item_service(session: AsyncSession = Depends(get_db_session)) -> ItemService:
    """Dependency injector for ItemService."""
    return ItemService(session)


@router.get(
    "/",
    response_model=list[ItemRead],
    summary="List items",
    description="List items with basic pagination.",
    operation_id="list_items",
)
async def list_items(
    service: ItemService = Depends(get_item_service),
    limit: int = Query(default=50, ge=1, le=200, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> list[ItemRead]:
    """List items endpoint."""
    return await service.list_items(limit=limit, offset=offset)


@router.get(
    "/{item_id}",
    response_model=ItemRead,
    summary="Get item",
    description="Get a single item by id.",
    operation_id="get_item",
)
async def get_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
) -> ItemRead:
    """Get item endpoint."""
    try:
        return await service.get_item_or_404(item_id)
    except NotFoundError as e:
        raise http_404(str(e)) from e


@router.post(
    "/",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create item",
    description="Create a new item.",
    operation_id="create_item",
)
async def create_item(
    payload: ItemCreate,
    service: ItemService = Depends(get_item_service),
) -> ItemRead:
    """Create item endpoint."""
    return await service.create_item(payload)


@router.patch(
    "/{item_id}",
    response_model=ItemRead,
    summary="Update item",
    description="Partially update an existing item.",
    operation_id="update_item",
)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    service: ItemService = Depends(get_item_service),
) -> ItemRead:
    """Update item endpoint."""
    try:
        return await service.update_item(item_id, payload)
    except NotFoundError as e:
        raise http_404(str(e)) from e


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    description="Delete an item by id.",
    operation_id="delete_item",
)
async def delete_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
) -> None:
    """Delete item endpoint."""
    try:
        await service.delete_item(item_id)
    except NotFoundError as e:
        raise http_404(str(e)) from e
"
