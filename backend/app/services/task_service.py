"""
Task service for CRUD operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project
from app.models.dataset_entry import DatasetEntry
from app.schemas.common import PaginationParams
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.base import BaseService
from app.services.exceptions import ConflictError, NotFoundError


class TaskService(BaseService[Task, TaskCreate, TaskUpdate]):
    """Service for Task CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Task)

    async def get_list_for_project(
        self,
        project: Project,
        pagination: PaginationParams,
        status: str | None = None,
        has_candidates: bool | None = None,
        has_accepted: bool | None = None,
        min_score: int | None = None,
    ) -> tuple[list[Task], int]:
        """Get tasks for a project with filtering."""
        filters: dict[str, Any] = {"project_id": project.id}

        if status:
            filters["status"] = status

        items, total = await self.get_list(pagination, filters)

        # Post-filtering for boolean conditions
        if has_candidates is not None:
            if has_candidates:
                items = [t for t in items if t.candidate_count > 0]
            else:
                items = [t for t in items if t.candidate_count == 0]

        if has_accepted is not None:
            if has_accepted:
                items = [t for t in items if t.accepted_wikidata_id is not None]
            else:
                items = [t for t in items if t.accepted_wikidata_id is None]

        if min_score is not None:
            items = [t for t in items if t.highest_score and t.highest_score >= min_score]

        return items, total

    async def create_for_project(
        self,
        project: Project,
        entry: DatasetEntry,
        data: TaskCreate,
    ) -> Task:
        """Create task for a project with uniqueness validation."""
        # Check if task already exists for this project/entry combo
        existing = await self._get_by_project_and_entry(project.id, entry.id)
        if existing:
            raise ConflictError(
                "Task",
                "project_uuid/dataset_entry_uuid",
                f"{data.project_uuid}/{data.dataset_entry_uuid}",
            )

        create_data = data.model_dump(exclude={"project_uuid", "dataset_entry_uuid"})
        create_data["project_id"] = project.id
        create_data["dataset_entry_id"] = entry.id

        db_obj = Task(**create_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj

    async def _get_by_project_and_entry(
        self, project_id: int, entry_id: int
    ) -> Task | None:
        """Get task by project and entry (internal helper)."""
        stmt = select(Task).where(
            Task.project_id == project_id,
            Task.dataset_entry_id == entry_id,
            Task.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_project_for_task(self, task: Task) -> Project | None:
        """Get the project for a task."""
        stmt = select(Project).where(
            Project.id == task.project_id,
            Project.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_entry_for_task(self, task: Task) -> DatasetEntry | None:
        """Get the dataset entry for a task."""
        stmt = select(DatasetEntry).where(
            DatasetEntry.id == task.dataset_entry_id,
            DatasetEntry.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def skip_task(self, task: Task) -> Task:
        """Mark task as skipped."""
        task.status = "skipped"
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task


def get_task_service(db: AsyncSession) -> TaskService:
    """Factory function for TaskService."""
    return TaskService(db)
