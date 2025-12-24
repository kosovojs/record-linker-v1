"""
DatasetEntry service for CRUD operations.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.dataset_entry import DatasetEntry
from app.schemas.common import PaginationParams
from app.schemas.dataset_entry import DatasetEntryCreate, DatasetEntryUpdate
from app.services.base import BaseService
from app.services.exceptions import ConflictError


class EntryService(BaseService[DatasetEntry, DatasetEntryCreate, DatasetEntryUpdate]):
    """Service for DatasetEntry CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, DatasetEntry)

    async def get_by_external_id(
        self, dataset_id: int, external_id: str
    ) -> DatasetEntry | None:
        """Get entry by external_id within a dataset."""
        stmt = select(DatasetEntry).where(
            DatasetEntry.dataset_id == dataset_id,
            DatasetEntry.external_id == external_id,
            DatasetEntry.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list_for_dataset(
        self,
        dataset: Dataset,
        pagination: PaginationParams,
        search: str | None = None,
    ) -> tuple[list[DatasetEntry], int]:
        """Get entries for a specific dataset with pagination and search."""
        from sqlalchemy import func

        # Build base query with all filters at SQL level
        base_query = select(DatasetEntry).where(
            DatasetEntry.dataset_id == dataset.id,
            DatasetEntry.deleted_at.is_(None),
        )

        # Apply search filter (ILIKE on display_name)
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.where(
                DatasetEntry.display_name.ilike(search_pattern)
            )

        # Count total with all filters applied
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        paginated_query = (
            base_query
            .order_by(DatasetEntry.created_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(paginated_query)
        items = list(result.scalars().all())

        return items, total

    async def create_for_dataset(
        self,
        dataset: Dataset,
        data: DatasetEntryCreate,
    ) -> DatasetEntry:
        """Create entry for a dataset with external_id uniqueness validation."""
        existing = await self.get_by_external_id(dataset.id, data.external_id)
        if existing:
            raise ConflictError("Entry", "external_id", data.external_id)

        create_data = data.model_dump(exclude={"dataset_uuid"})
        create_data["dataset_id"] = dataset.id

        db_obj = DatasetEntry(**create_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def update_with_validation(
        self,
        db_obj: DatasetEntry,
        data: DatasetEntryUpdate,
    ) -> DatasetEntry:
        """Update entry with external_id uniqueness validation."""
        if data.external_id and data.external_id != db_obj.external_id:
            existing = await self.get_by_external_id(
                db_obj.dataset_id, data.external_id
            )
            if existing:
                raise ConflictError("Entry", "external_id", data.external_id)
        return await self.update(db_obj, data)

    async def bulk_create_for_dataset(
        self,
        dataset: Dataset,
        entries: list[DatasetEntryCreate],
    ) -> list[DatasetEntry]:
        """
        Bulk create entries for a dataset (all-or-nothing transaction).

        Raises ConflictError if any external_id already exists.
        """
        # Batch-fetch all existing external IDs to avoid N+1 queries
        external_ids = [e.external_id for e in entries]
        existing_stmt = select(DatasetEntry.external_id).where(
            DatasetEntry.dataset_id == dataset.id,
            DatasetEntry.external_id.in_(external_ids),
            DatasetEntry.deleted_at.is_(None),
        )
        existing_result = await self.db.execute(existing_stmt)
        existing_ids = set(existing_result.scalars().all())

        # Check for conflicts
        conflicts = [eid for eid in external_ids if eid in existing_ids]
        if conflicts:
            raise ConflictError("Entry", "external_id", conflicts[0])

        # Create all entries
        created = []
        for data in entries:
            create_data = data.model_dump(exclude={"dataset_uuid"})
            create_data["dataset_id"] = dataset.id
            db_obj = DatasetEntry(**create_data)
            self.db.add(db_obj)
            created.append(db_obj)

        await self.db.commit()
        for obj in created:
            await self.db.refresh(obj)

        return created

    async def get_dataset_for_entry(self, entry: DatasetEntry) -> Dataset | None:
        """Get the dataset for an entry."""
        stmt = select(Dataset).where(
            Dataset.id == entry.dataset_id,
            Dataset.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


def get_entry_service(db: AsyncSession) -> EntryService:
    """Factory function for EntryService."""
    return EntryService(db)
