"""
Project service for CRUD and workflow operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.dataset import Dataset
from app.schemas.common import PaginationParams
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.base import BaseService


class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    """Service for Project CRUD and workflow operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Project)

    async def get_list_filtered(
        self,
        pagination: PaginationParams,
        status: str | None = None,
        dataset_uuid: UUID | None = None,
    ) -> tuple[list[Project], int]:
        """Get projects with optional filters."""
        filters: dict[str, Any] = {}

        if status:
            filters["status"] = status

        # Handle dataset_uuid filter - need to lookup dataset_id
        if dataset_uuid:
            dataset_stmt = select(Dataset.id).where(
                Dataset.uuid == dataset_uuid,
                Dataset.deleted_at.is_(None),
            )
            dataset_result = await self.db.execute(dataset_stmt)
            dataset_id = dataset_result.scalar_one_or_none()
            if dataset_id:
                filters["dataset_id"] = dataset_id
            else:
                # Dataset not found, return empty
                return [], 0

        return await self.get_list(pagination, filters)

    async def create_with_dataset(
        self,
        data: ProjectCreate,
        dataset: Dataset,
    ) -> Project:
        """Create project with resolved dataset reference."""
        create_data = data.model_dump(exclude={"dataset_uuid", "owner_uuid"})
        create_data["dataset_id"] = dataset.id
        # owner_id is nullable per user decision, leave as None for now

        db_obj = Project(**create_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def get_dataset_for_project(self, project: Project) -> Dataset | None:
        """Get the dataset associated with a project."""
        stmt = select(Dataset).where(
            Dataset.id == project.dataset_id,
            Dataset.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


def get_project_service(db: AsyncSession) -> ProjectService:
    """Factory function for ProjectService."""
    return ProjectService(db)
