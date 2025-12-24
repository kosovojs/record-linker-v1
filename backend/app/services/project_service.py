"""
Project service for CRUD and workflow operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import case, func, insert, select, update
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
        chunk_size: int = 1000,
    ) -> tuple[int, str]:
        """
        Start a project by creating tasks for entries.

        Per RQ2: Requires either explicit entry_uuids or all_entries=True flag.
        Per RQ1: Project status becomes pending_search.

        Uses chunked processing and bulk insert for scalability with large datasets.

        Args:
            project: The project to start
            entry_uuids: Optional list of specific entry UUIDs to process
            all_entries: If True, process all entries in the dataset
            chunk_size: Number of entries to process per batch (default 1000)

        Returns: (tasks_created, new_status)
        """

        if not entry_uuids and not all_entries:
            raise ValidationError(
                "Either 'entry_uuids' or 'all_entries: true' is required"
            )

        # Build query for entry IDs only (not full objects) for memory efficiency
        if all_entries:
            entry_stmt = select(DatasetEntry.id).where(
                DatasetEntry.dataset_id == project.dataset_id,
                DatasetEntry.deleted_at.is_(None),
            )
        else:
            entry_stmt = select(DatasetEntry.id).where(
                DatasetEntry.uuid.in_(entry_uuids),
                DatasetEntry.dataset_id == project.dataset_id,
                DatasetEntry.deleted_at.is_(None),
            )

        # Batch-fetch all existing task entry IDs to avoid duplicates
        existing_stmt = select(Task.dataset_entry_id).where(
            Task.project_id == project.id,
            Task.deleted_at.is_(None),
        )
        existing_result = await self.db.execute(existing_stmt)
        existing_entry_ids = set(existing_result.scalars().all())

        # Stream entry IDs in chunks to avoid OOM with large datasets
        result = await self.db.stream_scalars(entry_stmt)

        tasks_created = 0
        batch: list[dict] = []
        has_entries = False

        async for entry_id in result:
            has_entries = True
            if entry_id not in existing_entry_ids:
                batch.append({
                    "project_id": project.id,
                    "dataset_entry_id": entry_id,
                    "status": TaskStatus.NEW,
                    "candidate_count": 0,
                    "extra_data": {},
                })

                # Bulk insert when batch reaches chunk_size
                if len(batch) >= chunk_size:
                    await self.db.execute(insert(Task), batch)
                    tasks_created += len(batch)
                    batch = []

        # Insert remaining batch
        if batch:
            await self.db.execute(insert(Task), batch)
            tasks_created += len(batch)

        if not has_entries:
            raise ValidationError("No entries found to create tasks for")

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

        Uses bulk UPDATE for scalability - no objects loaded into memory.

        Criteria options: "failed", "no_candidates", "no_accepted"
        """

        if not criteria and not task_uuids:
            raise ValidationError(
                "Either 'criteria' or 'task_uuids' is required"
            )

        # Build WHERE conditions for the bulk update
        conditions = [
            Task.project_id == project.id,
            Task.deleted_at.is_(None),
        ]

        if task_uuids:
            conditions.append(Task.uuid.in_(task_uuids))
        elif criteria == "failed":
            conditions.append(Task.status == TaskStatus.FAILED)
        elif criteria == "no_candidates":
            conditions.append(Task.status == TaskStatus.NO_CANDIDATES_FOUND)
        elif criteria == "no_accepted":
            conditions.extend([
                Task.accepted_wikidata_id.is_(None),
                Task.status.in_([
                    TaskStatus.AWAITING_REVIEW,
                    TaskStatus.REVIEWED,
                ]),
            ])
        else:
            raise ValidationError(f"Invalid criteria: {criteria}")

        # Bulk update - no ORM objects loaded into memory
        stmt = (
            update(Task)
            .where(*conditions)
            .values(
                status=TaskStatus.NEW,
                accepted_wikidata_id=None,
                accepted_candidate_id=None,
                error_message=None,
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount

    async def get_stats(self, project: Project) -> dict:
        """
        Compute project statistics on-the-fly.

        Optimized to use only 2 queries with CASE-based conditional aggregation:
        - Query 1: All task stats in one aggregate query
        - Query 2: All candidate stats in one aggregate query

        Returns dict with: total_tasks, by_status, candidates, avg_score, progress_percent
        """

        # Query 1: Task stats - single query with CASE aggregation
        task_stats_stmt = select(
            func.count().label("total"),
            func.count(case((Task.status == TaskStatus.NEW, 1))).label("new"),
            func.count(case((Task.status == TaskStatus.QUEUED_FOR_PROCESSING, 1))).label("queued_for_processing"),
            func.count(case((Task.status == TaskStatus.PROCESSING, 1))).label("processing"),
            func.count(case((Task.status == TaskStatus.NO_CANDIDATES_FOUND, 1))).label("no_candidates_found"),
            func.count(case((Task.status == TaskStatus.AWAITING_REVIEW, 1))).label("awaiting_review"),
            func.count(case((Task.status == TaskStatus.REVIEWED, 1))).label("reviewed"),
            func.count(case((Task.status == TaskStatus.AUTO_CONFIRMED, 1))).label("auto_confirmed"),
            func.count(case((Task.status == TaskStatus.SKIPPED, 1))).label("skipped"),
            func.count(case((Task.status == TaskStatus.FAILED, 1))).label("failed"),
            func.count(case((Task.status == TaskStatus.KNOWLEDGE_BASED, 1))).label("knowledge_based"),
        ).where(
            Task.project_id == project.id,
            Task.deleted_at.is_(None),
        )
        task_result = await self.db.execute(task_stats_stmt)
        task_row = task_result.one()

        total_tasks = task_row.total or 0

        # Build by_status dict, only include non-zero counts
        by_status = {}
        status_mapping = {
            TaskStatus.NEW: task_row.new,
            TaskStatus.QUEUED_FOR_PROCESSING: task_row.queued_for_processing,
            TaskStatus.PROCESSING: task_row.processing,
            TaskStatus.NO_CANDIDATES_FOUND: task_row.no_candidates_found,
            TaskStatus.AWAITING_REVIEW: task_row.awaiting_review,
            TaskStatus.REVIEWED: task_row.reviewed,
            TaskStatus.AUTO_CONFIRMED: task_row.auto_confirmed,
            TaskStatus.SKIPPED: task_row.skipped,
            TaskStatus.FAILED: task_row.failed,
            TaskStatus.KNOWLEDGE_BASED: task_row.knowledge_based,
        }
        for status, count in status_mapping.items():
            if count:
                by_status[str(status)] = count

        # Query 2: Candidate stats - single query with CASE aggregation
        task_ids_subquery = select(Task.id).where(
            Task.project_id == project.id,
            Task.deleted_at.is_(None),
        ).scalar_subquery()

        candidate_stats_stmt = select(
            func.count().label("total"),
            func.count(case((MatchCandidate.status == CandidateStatus.ACCEPTED, 1))).label("accepted"),
            func.count(case((MatchCandidate.status == CandidateStatus.REJECTED, 1))).label("rejected"),
            func.avg(case((MatchCandidate.status == CandidateStatus.ACCEPTED, MatchCandidate.score))).label("avg_score"),
        ).where(
            MatchCandidate.task_id.in_(task_ids_subquery),
            MatchCandidate.deleted_at.is_(None),
        )
        candidate_result = await self.db.execute(candidate_stats_stmt)
        candidate_row = candidate_result.one()

        # Progress percent (reviewed + skipped tasks / total)
        completed_count = (task_row.reviewed or 0) + (task_row.skipped or 0)
        progress_percent = (completed_count / total_tasks * 100) if total_tasks > 0 else 0.0

        return {
            "total_tasks": total_tasks,
            "by_status": by_status,
            "candidates": {
                "total": candidate_row.total or 0,
                "accepted": candidate_row.accepted or 0,
                "rejected": candidate_row.rejected or 0,
            },
            "avg_score": round(candidate_row.avg_score, 1) if candidate_row.avg_score else None,
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

    async def soft_delete(self, db_obj: Project) -> Project:
        """
        Soft delete a project with cascade to Tasks and Candidates.

        This overrides the base soft_delete to ensure referential integrity.
        """
        from app.models.base import utc_now

        # Get all tasks for this project
        task_ids_stmt = select(Task.id).where(
            Task.project_id == db_obj.id,
            Task.deleted_at.is_(None),
        )
        task_result = await self.db.execute(task_ids_stmt)
        task_ids = list(task_result.scalars().all())

        if task_ids:
            # Soft delete all candidates for these tasks
            now = utc_now()
            for task_id in task_ids:
                candidates_stmt = select(MatchCandidate).where(
                    MatchCandidate.task_id == task_id,
                    MatchCandidate.deleted_at.is_(None),
                )
                candidates_result = await self.db.execute(candidates_stmt)
                for candidate in candidates_result.scalars().all():
                    candidate.deleted_at = now
                    self.db.add(candidate)

            # Soft delete all tasks
            tasks_stmt = select(Task).where(
                Task.project_id == db_obj.id,
                Task.deleted_at.is_(None),
            )
            tasks_result = await self.db.execute(tasks_stmt)
            for task in tasks_result.scalars().all():
                task.deleted_at = now
                self.db.add(task)

        # Soft delete the project itself
        db_obj.soft_delete()
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        return db_obj


def get_project_service(db: AsyncSession) -> ProjectService:
    """Factory function for ProjectService."""
    return ProjectService(db)
