from __future__ import annotations

from fastapi import APIRouter

from src.api.routes.v1.users import router as users_router

router = APIRouter()
router.include_router(users_router, prefix="/users", tags=["Users"])
