from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends

from src.db.session import AsyncSession, get_db_session
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService


# PUBLIC_INTERFACE
def get_user_service(db: AsyncSession = Depends(get_db_session)) -> UserService:
    """Create a UserService instance wired with a repository and request-scoped DB session."""
    repo = UserRepository(db)
    return UserService(repo)
