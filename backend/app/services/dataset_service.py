"""
Dataset service for CRUD operations.
"""

from __future__ import annotations

from typing import Any

import re
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.schemas.common import PaginationParams
from app.schemas.dataset import DatasetCreate, DatasetUpdate
from app.services.base import BaseService
from app.services.exceptions import ConflictError


def slugify(text: str) -> str:
    """Create a URL-friendly slug from text."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


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
        """Get datasets with optional filters including search."""

        # Build base query with all filters at SQL level
        base_query = select(Dataset).where(Dataset.deleted_at.is_(None))

        if source_type:
            base_query = base_query.where(Dataset.source_type == source_type)
        if entity_type:
            base_query = base_query.where(Dataset.entity_type == entity_type)

        # Apply search filter (ILIKE on name and description)
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Dataset.name.ilike(search_pattern),
                    Dataset.description.ilike(search_pattern),
                )
            )

        # Count total with all filters applied
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        paginated_query = (
            base_query
            .order_by(Dataset.created_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(paginated_query)
        items = list(result.scalars().all())

        return items, total

    async def create_with_validation(self, data: DatasetCreate) -> Dataset:
        """Create dataset with slug uniqueness validation."""
        # Auto-generate slug if not provided
        if not data.slug:
            data.slug = slugify(data.name)

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
