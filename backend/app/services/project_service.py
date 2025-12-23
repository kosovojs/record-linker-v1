"""
Project service for CRUD and workflow operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.dataset import Dataset
from app.schemas.common import PaginationParams
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.base import BaseService


class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    """Service for Project CRUD and workflow operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Project)

    async def get_with_dataset(self, uuid: UUID) -> tuple[Project | None, Dataset | None]:
        """Get project with its dataset in a single query."""
        stmt = (
            select(Project, Dataset)
            .outerjoin(Dataset, Project.dataset_id == Dataset.id)
            .where(Project.uuid == uuid, Project.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if row:
            return row[0], row[1]
        return None, None

    async def get_list_with_datasets(
        self,
        pagination: PaginationParams,
        status: str | None = None,
        dataset_uuid: UUID | None = None,
    ) -> tuple[list[ProjectRead], int]:
        """Get projects with dataset UUIDs in a single query (no N+1)."""
        # Base query
        base_query = (
            select(Project, Dataset.uuid.label("dataset_uuid"))
            .outerjoin(Dataset, Project.dataset_id == Dataset.id)
            .where(Project.deleted_at.is_(None))
        )

        if status:
            base_query = base_query.where(Project.status == status)

        if dataset_uuid:
            base_query = base_query.where(Dataset.uuid == dataset_uuid)

        # Count total
        count_stmt = select(func.count()).select_from(
            base_query.with_only_columns(Project.id).subquery()
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        paginated = (
            base_query
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(paginated)
        rows = result.all()

        # Build ProjectRead objects with dataset_uuid already populated
        project_reads = []
        for project, ds_uuid in rows:
            project_read = ProjectRead.model_validate(project)
            project_read.dataset_uuid = ds_uuid
            project_reads.append(project_read)

        return project_reads, total

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
