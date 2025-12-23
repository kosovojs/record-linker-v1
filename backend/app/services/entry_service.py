"""
DatasetEntry service for CRUD operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

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
        """Get entries for a specific dataset with pagination."""
        filters: dict[str, Any] = {"dataset_id": dataset.id}
        return await self.get_list(pagination, filters)

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
        created = []
        for data in entries:
            existing = await self.get_by_external_id(dataset.id, data.external_id)
            if existing:
                raise ConflictError("Entry", "external_id", data.external_id)

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
