from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.api.errors.exceptions import ConflictError
from src.db.session import AsyncSession
from src.models.user import User


class UserRepository:
    """Data access layer for User."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, user: User) -> User:
        """Persist a new user."""
        self._db.add(user)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            # Typically unique constraint violation on email
            raise ConflictError("User with this email already exists") from exc
        return user

    async def get(self, user_id: str) -> User | None:
        """Get user by id."""
        stmt = select(User).where(User.id == user_id)
        res = await self._db.execute(stmt)
        return res.scalar_one_or_none()

    async def list(self, limit: int, offset: int) -> tuple[list[User], int]:
        """List users with pagination and total count."""
        items_stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        total_stmt = select(func.count()).select_from(User)

        items_res = await self._db.execute(items_stmt)
        total_res = await self._db.execute(total_stmt)

        return list(items_res.scalars().all()), int(total_res.scalar_one())
