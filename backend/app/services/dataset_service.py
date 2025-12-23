"""
Dataset service for CRUD operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.schemas.common import PaginationParams
from app.schemas.dataset import DatasetCreate, DatasetUpdate
from app.services.base import BaseService


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

        # For search, we'll handle it separately with ILIKE
        # For now, use basic filters
        return await self.get_list(pagination, filters)


def get_dataset_service(db: AsyncSession) -> DatasetService:
    """Factory function for DatasetService."""
    return DatasetService(db)
