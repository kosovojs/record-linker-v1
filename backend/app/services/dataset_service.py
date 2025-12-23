"""
Dataset service for CRUD operations.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.schemas.common import PaginationParams
from app.schemas.dataset import DatasetCreate, DatasetUpdate
from app.services.base import BaseService
from app.services.exceptions import ConflictError


class DatasetService(BaseService[Dataset, DatasetCreate, DatasetUpdate]):
    """Service for Dataset CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Dataset)

    async def get_by_slug(self, slug: str) -> Dataset | None:
        """Get dataset by unique slug."""
        stmt = select(Dataset).where(
            Dataset.slug == slug,
            Dataset.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list_filtered(
        self,
        pagination: PaginationParams,
        source_type: str | None = None,
        entity_type: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Dataset], int]:
        """Get datasets with optional filters."""
        filters: dict[str, Any] = {}

        if source_type:
            filters["source_type"] = source_type
        if entity_type:
            filters["entity_type"] = entity_type

        return await self.get_list(pagination, filters)

    async def create_with_validation(self, data: DatasetCreate) -> Dataset:
        """Create dataset with slug uniqueness validation."""
        existing = await self.get_by_slug(data.slug)
        if existing:
            raise ConflictError("Dataset", "slug", data.slug)
        return await self.create(data)

    async def update_with_validation(
        self, db_obj: Dataset, data: DatasetUpdate
    ) -> Dataset:
        """Update dataset with slug uniqueness validation."""
        if data.slug and data.slug != db_obj.slug:
            existing = await self.get_by_slug(data.slug)
            if existing:
                raise ConflictError("Dataset", "slug", data.slug)
        return await self.update(db_obj, data)


def get_dataset_service(db: AsyncSession) -> DatasetService:
    """Factory function for DatasetService."""
    return DatasetService(db)
