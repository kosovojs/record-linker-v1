"""
API dependencies for FastAPI route handlers.

Provides:
- Database session dependency
- Pagination parameter dependency
- Current user dependency (stub for now)
- Common query filters
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationParams

__all__ = [
    "DbSession",
    "Pagination",
    "get_pagination",
]


# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Items per page (max 100)",
    ),
) -> PaginationParams:
    """Dependency for pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)


# Type alias for pagination dependency
Pagination = Annotated[PaginationParams, Depends(get_pagination)]


# Placeholder for authentication - will be implemented properly later
# async def get_current_user(
#     db: DbSession,
#     token: str = Depends(oauth2_scheme),
# ) -> User:
#     """Get the current authenticated user."""
#     ...
#
# CurrentUser = Annotated[User, Depends(get_current_user)]
