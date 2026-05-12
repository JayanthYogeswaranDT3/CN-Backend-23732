from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.items.models import Item
from app.modules.items.schemas import ItemCreate, ItemUpdate


class ItemRepository:
    """Repository for Item persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_items(self, *, limit: int = 50, offset: int = 0) -> list[Item]:
        stmt = select(Item).order_by(Item.id.asc()).limit(limit).offset(offset)
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def get_item(self, item_id: int) -> Item | None:
        return await self._session.get(Item, item_id)

    async def create_item(self, payload: ItemCreate) -> Item:
        item = Item(name=payload.name, description=payload.description)
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def update_item(self, item: Item, payload: ItemUpdate) -> Item:
        if payload.name is not None:
            item.name = payload.name
        if payload.description is not None:
            item.description = payload.description

        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def delete_item(self, item: Item) -> None:
        await self._session.delete(item)
        await self._session.commit()
"
