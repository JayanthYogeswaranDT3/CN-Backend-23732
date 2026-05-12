from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from src.api.deps import get_user_service
from src.schemas.common import Paginated
from src.schemas.user import UserCreate, UserRead
from src.services.user_service import UserService

router = APIRouter()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    description="Creates a new user.",
)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Create a new user (sample CRUD endpoint)."""
    user = await service.create_user(payload)
    return UserRead.model_validate(user)


@router.get(
    "",
    response_model=Paginated[UserRead],
    status_code=status.HTTP_200_OK,
    summary="List users",
    description="Lists users with simple offset pagination.",
)
async def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: UserService = Depends(get_user_service),
) -> Paginated[UserRead]:
    """List users with basic pagination."""
    items, total = await service.list_users(limit=limit, offset=offset)
    return Paginated[UserRead](
        items=[UserRead.model_validate(u) for u in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get user by id",
    description="Fetch a user by UUID.",
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Get a user by id (sample CRUD endpoint)."""
    user = await service.get_user(user_id)
    return UserRead.model_validate(user)
