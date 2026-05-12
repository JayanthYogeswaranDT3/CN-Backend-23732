from __future__ import annotations

from fastapi import APIRouter

from app.modules.items.router import router as items_router

router = APIRouter()
router.include_router(items_router, prefix="/items", tags=["items"])
"
