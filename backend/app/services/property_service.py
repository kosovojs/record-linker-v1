"""
PropertyDefinition service for CRUD operations.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property_definition import PropertyDefinition
from app.schemas.common import PaginationParams
from app.schemas.property_definition import (
    PropertyDefinitionCreate,
    PropertyDefinitionUpdate,
)
from app.services.base import BaseService


class PropertyDefinitionService(
    BaseService[PropertyDefinition, PropertyDefinitionCreate, PropertyDefinitionUpdate]
):
    """Service for PropertyDefinition CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, PropertyDefinition)

    async def get_by_name(self, name: str) -> PropertyDefinition | None:
        """Get property definition by unique name."""
        stmt = select(PropertyDefinition).where(
            PropertyDefinition.name == name,
            PropertyDefinition.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list_filtered(
        self,
        pagination: PaginationParams,
        data_type: str | None = None,
        wikidata_only: bool = False,
    ) -> tuple[list[PropertyDefinition], int]:
        """Get property definitions with optional filters."""
        filters: dict[str, Any] = {}

        if data_type:
            filters["data_type_hint"] = data_type

        items, total = await self.get_list(pagination, filters)

        # Apply wikidata_only filter (can't use simple equality)
        if wikidata_only:
            items = [item for item in items if item.wikidata_property is not None]
            # Note: This affects accuracy of total count, but acceptable for now

        return items, total


def get_property_service(db: AsyncSession) -> PropertyDefinitionService:
    """Factory function for PropertyDefinitionService."""
    return PropertyDefinitionService(db)
