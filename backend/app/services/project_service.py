"""
Project service for CRUD and workflow operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.dataset_entry import DatasetEntry
from app.models.match_candidate import MatchCandidate
from app.models.project import Project
from app.models.task import Task
from app.schemas.common import PaginationParams
from app.schemas.enums import CandidateStatus, ProjectStatus, TaskStatus
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.base import BaseService
from app.services.exceptions import ValidationError


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

    # ========================================================================
    # Workflow methods
    # ========================================================================

    async def start_project(
        self,
        project: Project,
        entry_uuids: list[UUID] | None = None,
        all_entries: bool = False,
    ) -> tuple[int, str]:
        """
        Start a project by creating tasks for entries.

        Per RQ2: Requires either explicit entry_uuids or all_entries=True flag.
        Per RQ1: Project status becomes pending_search.

        Returns: (tasks_created, new_status)
        """

        if not entry_uuids and not all_entries:
            raise ValidationError(
                "Either 'entry_uuids' or 'all_entries: true' is required"
            )

        # Get entries from dataset
        if all_entries:
            stmt = select(DatasetEntry).where(
                DatasetEntry.dataset_id == project.dataset_id,
                DatasetEntry.deleted_at.is_(None),
            )
        else:
            stmt = select(DatasetEntry).where(
                DatasetEntry.uuid.in_(entry_uuids),
                DatasetEntry.dataset_id == project.dataset_id,
                DatasetEntry.deleted_at.is_(None),
            )

        result = await self.db.execute(stmt)
        entries = list(result.scalars().all())

        if not entries:
            raise ValidationError("No entries found to create tasks for")

        # Create tasks for each entry (skip if already exists)
        tasks_created = 0
        for entry in entries:
            existing_stmt = select(Task).where(
                Task.project_id == project.id,
                Task.dataset_entry_id == entry.id,
                Task.deleted_at.is_(None),
            )
            existing = await self.db.execute(existing_stmt)
            if existing.scalar_one_or_none() is None:
                task = Task(project_id=project.id, dataset_entry_id=entry.id)
                self.db.add(task)
                tasks_created += 1

        # Update project status
        project.status = ProjectStatus.PENDING_SEARCH
        self.db.add(project)

        await self.db.commit()
        await self.db.refresh(project)

        return tasks_created, project.status

    async def rerun_tasks(
        self,
        project: Project,
        criteria: str | None = None,
        task_uuids: list[UUID] | None = None,
    ) -> int:
        """
        Reset tasks for reprocessing based on criteria.

        Criteria options: "failed", "no_candidates", "no_accepted"
        """

        if not criteria and not task_uuids:
            raise ValidationError(
                "Either 'criteria' or 'task_uuids' is required"
            )

        if task_uuids:
            # Reset specific tasks
            stmt = select(Task).where(
                Task.uuid.in_(task_uuids),
                Task.project_id == project.id,
                Task.deleted_at.is_(None),
            )
        else:
            # Build query based on criteria
            base_stmt = select(Task).where(
                Task.project_id == project.id,
                Task.deleted_at.is_(None),
            )

            if criteria == "failed":
                stmt = base_stmt.where(Task.status == TaskStatus.FAILED)
            elif criteria == "no_candidates":
                stmt = base_stmt.where(Task.status == TaskStatus.NO_CANDIDATES_FOUND)
            elif criteria == "no_accepted":
                stmt = base_stmt.where(
                    Task.accepted_wikidata_id.is_(None),
                    Task.status.in_([
                        TaskStatus.AWAITING_REVIEW,
                        TaskStatus.REVIEWED,
                    ]),
                )
            else:
                raise ValidationError(f"Invalid criteria: {criteria}")

        result = await self.db.execute(stmt)
        tasks = list(result.scalars().all())

        tasks_reset = 0
        for task in tasks:
            task.status = TaskStatus.NEW
            task.accepted_wikidata_id = None
            task.accepted_candidate_id = None
            task.error_message = None
            self.db.add(task)
            tasks_reset += 1

        await self.db.commit()
        return tasks_reset

    async def get_stats(self, project: Project) -> dict:
        """
        Compute project statistics on-the-fly.

        Returns dict with: total_tasks, by_status, candidates, avg_score, progress_percent
        """

        # Total tasks
        total_stmt = select(func.count()).where(
            Task.project_id == project.id,
            Task.deleted_at.is_(None),
        )
        total_result = await self.db.execute(total_stmt)
        total_tasks = total_result.scalar() or 0

        # Tasks by status
        status_stmt = (
            select(Task.status, func.count())
            .where(Task.project_id == project.id, Task.deleted_at.is_(None))
            .group_by(Task.status)
        )
        status_result = await self.db.execute(status_stmt)
        by_status = {str(row[0]): row[1] for row in status_result.all()}

        # Candidate stats (from tasks in this project)
        task_ids_stmt = select(Task.id).where(
            Task.project_id == project.id,
            Task.deleted_at.is_(None),
        )

        candidates_total_stmt = select(func.count()).where(
            MatchCandidate.task_id.in_(task_ids_stmt),
            MatchCandidate.deleted_at.is_(None),
        )
        candidates_total_result = await self.db.execute(candidates_total_stmt)
        total_candidates = candidates_total_result.scalar() or 0

        accepted_stmt = select(func.count()).where(
            MatchCandidate.task_id.in_(task_ids_stmt),
            MatchCandidate.status == CandidateStatus.ACCEPTED,
            MatchCandidate.deleted_at.is_(None),
        )
        accepted_result = await self.db.execute(accepted_stmt)
        accepted_candidates = accepted_result.scalar() or 0

        rejected_stmt = select(func.count()).where(
            MatchCandidate.task_id.in_(task_ids_stmt),
            MatchCandidate.status == CandidateStatus.REJECTED,
            MatchCandidate.deleted_at.is_(None),
        )
        rejected_result = await self.db.execute(rejected_stmt)
        rejected_candidates = rejected_result.scalar() or 0

        # Average score of accepted candidates
        avg_stmt = select(func.avg(MatchCandidate.score)).where(
            MatchCandidate.task_id.in_(task_ids_stmt),
            MatchCandidate.status == CandidateStatus.ACCEPTED,
            MatchCandidate.deleted_at.is_(None),
        )
        avg_result = await self.db.execute(avg_stmt)
        avg_score = avg_result.scalar()

        # Progress percent (reviewed + skipped tasks / total)
        completed_count = by_status.get(TaskStatus.REVIEWED, 0) + by_status.get(TaskStatus.SKIPPED, 0)
        progress_percent = (completed_count / total_tasks * 100) if total_tasks > 0 else 0.0

        return {
            "total_tasks": total_tasks,
            "by_status": by_status,
            "candidates": {
                "total": total_candidates,
                "accepted": accepted_candidates,
                "rejected": rejected_candidates,
            },
            "avg_score": round(avg_score, 1) if avg_score else None,
            "progress_percent": round(progress_percent, 1),
        }

    async def get_approved_matches(self, project: Project) -> list[dict]:
        """
        Get list of approved matches for a project.

        Returns list of dicts with: task_uuid, entry_external_id, entry_display_name,
        wikidata_id, score
        """

        stmt = (
            select(
                Task.uuid.label("task_uuid"),
                DatasetEntry.external_id.label("entry_external_id"),
                DatasetEntry.display_name.label("entry_display_name"),
                MatchCandidate.wikidata_id,
                MatchCandidate.score,
            )
            .join(DatasetEntry, Task.dataset_entry_id == DatasetEntry.id)
            .join(MatchCandidate, Task.accepted_candidate_id == MatchCandidate.id)
            .where(
                Task.project_id == project.id,
                Task.accepted_wikidata_id.isnot(None),
                Task.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "task_uuid": str(row.task_uuid),
                "entry_external_id": row.entry_external_id,
                "entry_display_name": row.entry_display_name,
                "wikidata_id": row.wikidata_id,
                "score": row.score,
            }
            for row in rows
        ]


def get_project_service(db: AsyncSession) -> ProjectService:
    """Factory function for ProjectService."""
    return ProjectService(db)
