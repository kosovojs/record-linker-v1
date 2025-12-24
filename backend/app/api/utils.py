"""
Common utilities for API routes.

Provides helper functions to reduce boilerplate in route handlers.
"""

from __future__ import annotations

from typing import Any, NoReturn
from uuid import UUID

from fastapi import HTTPException, status

from app.services.base import BaseService
from app.services.exceptions import ConflictError, NotFoundError


def raise_not_found(entity_name: str) -> NoReturn:
    """Raise a 404 HTTPException for a not found entity."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity_name} not found",
    )


async def get_or_404[T](
    service: BaseService[T, Any, Any],
    uuid: UUID,
    entity_name: str,
) -> T:
    """
    Get entity by UUID or raise 404.

    Usage:
        dataset = await get_or_404(service, uuid, "Dataset")
    """
    entity = await service.get_by_uuid(uuid)
    if not entity:
        raise_not_found(entity_name)
    return entity


def handle_conflict_error(error: ConflictError) -> None:
    """Convert ConflictError to HTTPException."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=error.message,
    )


def handle_not_found_error(error: NotFoundError) -> None:
    """Convert NotFoundError to HTTPException."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error.message,
    )
