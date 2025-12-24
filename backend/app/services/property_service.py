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
from app.services.exceptions import ConflictError


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
        """Get property definitions with optional filters at SQL level."""
        from sqlalchemy import func

        # Build base query with all filters at SQL level
        base_query = select(PropertyDefinition).where(
            PropertyDefinition.deleted_at.is_(None),
        )

        if data_type:
            base_query = base_query.where(PropertyDefinition.data_type_hint == data_type)

        # Apply wikidata_only filter at SQL level
        if wikidata_only:
            base_query = base_query.where(PropertyDefinition.wikidata_property.isnot(None))

        # Count total with all filters applied
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        paginated_query = (
            base_query
            .order_by(PropertyDefinition.created_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(paginated_query)
        items = list(result.scalars().all())

        return items, total

    async def create_with_validation(
        self, data: PropertyDefinitionCreate
    ) -> PropertyDefinition:
        """Create property definition with name uniqueness validation."""
        existing = await self.get_by_name(data.name)
        if existing:
            raise ConflictError("Property", "name", data.name)
        return await self.create(data)

    async def update_with_validation(
        self, db_obj: PropertyDefinition, data: PropertyDefinitionUpdate
    ) -> PropertyDefinition:
        """Update property definition with name uniqueness validation."""
        if data.name and data.name != db_obj.name:
            existing = await self.get_by_name(data.name)
            if existing:
                raise ConflictError("Property", "name", data.name)
        return await self.update(db_obj, data)


def get_property_service(db: AsyncSession) -> PropertyDefinitionService:
    """Factory function for PropertyDefinitionService."""
    return PropertyDefinitionService(db)
