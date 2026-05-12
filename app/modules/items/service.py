from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.items.repository import ItemRepository
from app.modules.items.schemas import ItemCreate, ItemUpdate


class ItemService:
    """Service layer for Items."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ItemRepository(session)

    async def list_items(self, *, limit: int = 50, offset: int = 0):
        return await self._repo.list_items(limit=limit, offset=offset)

    async def get_item_or_404(self, item_id: int):
        item = await self._repo.get_item(item_id)
        if item is None:
            raise NotFoundError(f"Item {item_id} not found")
        return item

    async def create_item(self, payload: ItemCreate):
        return await self._repo.create_item(payload)

    async def update_item(self, item_id: int, payload: ItemUpdate):
        item = await self.get_item_or_404(item_id)
        return await self._repo.update_item(item, payload)

    async def delete_item(self, item_id: int) -> None:
        item = await self.get_item_or_404(item_id)
        await self._repo.delete_item(item)
"
