from __future__ import annotations

from sqlalchemy import text

from src.api.errors.exceptions import NotFoundError
from src.db.session import SessionLocal
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.utils.ids import new_uuid


class UserService:
    """Business logic for users (sample module)."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def create_user(self, payload: UserCreate) -> User:
        """Create a user."""
        user = User(
            id=new_uuid(),
            email=str(payload.email),
            full_name=payload.full_name,
        )
        return await self._repo.create(user)

    async def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        """List users."""
        return await self._repo.list(limit=limit, offset=offset)

    async def get_user(self, user_id: str) -> User:
        """Get user or raise NotFoundError."""
        user = await self._repo.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user


class DatabasePingService:
    """Small helper used by readiness check to verify DB connectivity."""

    @staticmethod
    async def ping() -> bool:
        """Ping the DB and return True if reachable."""
        try:
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
