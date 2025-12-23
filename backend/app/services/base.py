"""
Base service with common CRUD operations.

Provides async methods for:
- get_by_uuid()
- get_by_id()
- get_list() with pagination
- create()
- update()
- soft_delete()
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseTableModel
from app.schemas.common import PaginationParams

# Type variables for generic service
ModelType = TypeVar("ModelType", bound=BaseTableModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base service with CRUD operations.

    Usage:
        class DatasetService(BaseService[Dataset, DatasetCreate, DatasetUpdate]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, Dataset)
    """

    def __init__(self, db: AsyncSession, model: type[ModelType]):
        self.db = db
        self.model = model

    async def get_by_uuid(self, uuid: UUID) -> ModelType | None:
        """Get a single record by UUID (excludes soft-deleted)."""
        stmt = select(self.model).where(
            self.model.uuid == uuid,
            self.model.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: int) -> ModelType | None:
        """Get a single record by internal ID (excludes soft-deleted)."""
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        pagination: PaginationParams,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelType], int]:
        """
        Get paginated list of records.

        Returns:
            Tuple of (items, total_count)
        """
        # Base query excluding soft-deleted
        base_query = select(self.model).where(self.model.deleted_at.is_(None))

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    base_query = base_query.where(getattr(self.model, key) == value)

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        paginated_query = (
            base_query
            .order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(paginated_query)
        items = list(result.scalars().all())

        return items, total

    async def create(self, data: CreateSchemaType) -> ModelType:
        """Create a new record."""
        # Convert Pydantic model to dict, excluding unset fields
        create_data = data.model_dump(exclude_unset=True)

        # Create model instance
        db_obj = self.model(**create_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        data: UpdateSchemaType,
    ) -> ModelType:
        """Update an existing record."""
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def soft_delete(self, db_obj: ModelType) -> ModelType:
        """Soft delete a record by setting deleted_at."""
        db_obj.soft_delete()
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj
