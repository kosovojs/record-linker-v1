"""
Task service for CRUD operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_entry import DatasetEntry
from app.models.project import Project
from app.models.task import Task
from app.schemas.common import PaginationParams
from app.schemas.enums import TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.base import BaseService
from app.services.exceptions import ConflictError


class TaskService(BaseService[Task, TaskCreate, TaskUpdate]):
    """Service for Task CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Task)

    async def get_with_entry_uuid(self, uuid: UUID) -> tuple[Task | None, UUID | None]:
        """Get task with its entry UUID in single query."""
        stmt = (
            select(Task, DatasetEntry.uuid.label("entry_uuid"))
            .outerjoin(DatasetEntry, Task.dataset_entry_id == DatasetEntry.id)
            .where(Task.uuid == uuid, Task.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if row:
            return row[0], row[1]
        return None, None

    async def get_with_related_uuids(
        self, uuid: UUID
    ) -> tuple[Task | None, UUID | None, UUID | None]:
        """Get task with project and entry UUIDs in single query."""
        stmt = (
            select(
                Task,
                Project.uuid.label("project_uuid"),
                DatasetEntry.uuid.label("entry_uuid"),
            )
            .outerjoin(Project, Task.project_id == Project.id)
            .outerjoin(DatasetEntry, Task.dataset_entry_id == DatasetEntry.id)
            .where(Task.uuid == uuid, Task.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if row:
            return row[0], row[1], row[2]
        return None, None, None

    async def get_entry_uuids_for_tasks(self, tasks: list[Task]) -> dict[int, UUID]:
        """Batch fetch entry UUIDs for multiple tasks (N+1 prevention)."""
        if not tasks:
            return {}

        entry_ids = [t.dataset_entry_id for t in tasks if t.dataset_entry_id]
        if not entry_ids:
            return {}

        stmt = select(DatasetEntry.id, DatasetEntry.uuid).where(
            DatasetEntry.id.in_(entry_ids)
        )
        result = await self.db.execute(stmt)
        id_to_uuid = {row[0]: row[1] for row in result.all()}

        return {t.id: id_to_uuid.get(t.dataset_entry_id) for t in tasks}

    async def get_list_for_project(
        self,
        project: Project,
        pagination: PaginationParams,
        status: str | None = None,
        has_candidates: bool | None = None,
        has_accepted: bool | None = None,
        min_score: int | None = None,
    ) -> tuple[list[Task], int]:
        """Get tasks for a project with filtering at SQL level."""
        from sqlalchemy import func

        # Build base query with all filters at SQL level
        base_query = select(Task).where(
            Task.project_id == project.id,
            Task.deleted_at.is_(None),
        )

        # Apply status filter
        if status:
            base_query = base_query.where(Task.status == status)

        # Apply has_candidates filter at SQL level
        if has_candidates is not None:
            if has_candidates:
                base_query = base_query.where(Task.candidate_count > 0)
            else:
                base_query = base_query.where(Task.candidate_count == 0)

        # Apply has_accepted filter at SQL level
        if has_accepted is not None:
            if has_accepted:
                base_query = base_query.where(Task.accepted_wikidata_id.isnot(None))
            else:
                base_query = base_query.where(Task.accepted_wikidata_id.is_(None))

        # Apply min_score filter at SQL level
        if min_score is not None:
            base_query = base_query.where(
                Task.highest_score.isnot(None),
                Task.highest_score >= min_score,
            )

        # Count total with all filters applied
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        paginated_query = (
            base_query
            .order_by(Task.created_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(paginated_query)
        items = list(result.scalars().all())

        return items, total

    async def create_for_project(
        self,
        project: Project,
        entry: DatasetEntry,
        data: TaskCreate,
    ) -> Task:
        """Create task for a project with uniqueness validation."""
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
        task.status = TaskStatus.SKIPPED
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task


def get_task_service(db: AsyncSession) -> TaskService:
    """Factory function for TaskService."""
    return TaskService(db)
