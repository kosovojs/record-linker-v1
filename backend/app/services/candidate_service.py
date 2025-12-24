"""
Candidate service for CRUD operations and business logic.

Key methods:
- get_list_for_task() - List candidates (no pagination per spec)
- create_bulk() - Bulk create candidates
- accept_candidate() - Accept and update task
- reject_candidate() - Reject candidate
- bulk_update() - Bulk status updates
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_candidate import MatchCandidate
from app.models.task import Task
from app.schemas.enums import CandidateStatus, TaskStatus
from app.schemas.match_candidate import MatchCandidateCreate, MatchCandidateUpdate
from app.services.base import BaseService
from app.services.exceptions import ValidationError


class CandidateService(BaseService[MatchCandidate, MatchCandidateCreate, MatchCandidateUpdate]):
    """Service for MatchCandidate CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, MatchCandidate)

    async def get_list_for_task(self, task: Task) -> list[MatchCandidate]:
        """Get all candidates for a task (no pagination per spec)."""
        stmt = (
            select(MatchCandidate)
            .where(
                MatchCandidate.task_id == task.id,
                MatchCandidate.deleted_at.is_(None),
            )
            .order_by(MatchCandidate.score.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_with_task_uuid(self, uuid: UUID) -> tuple[MatchCandidate | None, UUID | None]:
        """Get candidate with its task UUID in single query."""
        stmt = (
            select(MatchCandidate, Task.uuid.label("task_uuid"))
            .outerjoin(Task, MatchCandidate.task_id == Task.id)
            .where(MatchCandidate.uuid == uuid, MatchCandidate.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if row:
            return row[0], row[1]
        return None, None

    async def get_task_uuids_for_candidates(
        self, candidates: list[MatchCandidate]
    ) -> dict[int, UUID]:
        """Batch fetch task UUIDs for multiple candidates (N+1 prevention)."""
        if not candidates:
            return {}

        task_ids = [c.task_id for c in candidates if c.task_id]
        if not task_ids:
            return {}

        stmt = select(Task.id, Task.uuid).where(Task.id.in_(task_ids))
        result = await self.db.execute(stmt)
        id_to_uuid = {row[0]: row[1] for row in result.all()}

        return {c.id: id_to_uuid.get(c.task_id) for c in candidates}

    async def create_for_task(
        self, task: Task, data: MatchCandidateCreate
    ) -> MatchCandidate:
        """Create a single candidate for a task."""
        create_data = data.model_dump(exclude={"task_uuid"})
        create_data["task_id"] = task.id

        db_obj = MatchCandidate(**create_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        # Update task candidate count and highest score
        await self._update_task_stats(task)

        return db_obj

    async def create_bulk(
        self, task: Task, candidates_data: list[MatchCandidateCreate]
    ) -> list[MatchCandidate]:
        """Bulk create candidates for a task (all-or-nothing)."""
        created = []
        for data in candidates_data:
            create_data = data.model_dump(exclude={"task_uuid"})
            create_data["task_id"] = task.id
            db_obj = MatchCandidate(**create_data)
            self.db.add(db_obj)
            created.append(db_obj)

        await self.db.commit()
        for obj in created:
            await self.db.refresh(obj)

        # Update task stats after bulk create
        await self._update_task_stats(task)

        return created

    async def accept_candidate(
        self, candidate: MatchCandidate, task: Task
    ) -> tuple[MatchCandidate, Task]:
        """
        Accept a candidate, updating task status.

        - Sets candidate status to accepted
        - Sets task status to reviewed
        - Sets task accepted_wikidata_id
        - Sets task accepted_candidate_id
        """
        if candidate.status != CandidateStatus.SUGGESTED:
            raise ValidationError(
                f"Cannot accept candidate with status '{candidate.status}'. "
                f"Only 'suggested' candidates can be accepted."
            )

        # Update candidate
        candidate.status = CandidateStatus.ACCEPTED
        candidate.reviewed_at = datetime.now(UTC)
        self.db.add(candidate)

        # Update task
        task.status = TaskStatus.REVIEWED
        task.accepted_wikidata_id = candidate.wikidata_id
        task.accepted_candidate_id = candidate.id
        task.reviewed_at = datetime.now(UTC)
        self.db.add(task)

        await self.db.commit()
        await self.db.refresh(candidate)
        await self.db.refresh(task)

        return candidate, task

    async def reject_candidate(self, candidate: MatchCandidate) -> MatchCandidate:
        """Reject a candidate."""
        if candidate.status != CandidateStatus.SUGGESTED:
            raise ValidationError(
                f"Cannot reject candidate with status '{candidate.status}'. "
                f"Only 'suggested' candidates can be rejected."
            )

        candidate.status = CandidateStatus.REJECTED
        candidate.reviewed_at = datetime.now(UTC)
        self.db.add(candidate)
        await self.db.commit()
        await self.db.refresh(candidate)

        return candidate

    async def bulk_update(
        self, candidates: list[MatchCandidate], updates: MatchCandidateUpdate
    ) -> list[MatchCandidate]:
        """
        Bulk update candidates (all-or-nothing).

        Uses a single UPDATE statement for efficiency instead of
        individual ORM updates.
        """
        if not candidates:
            return []

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            return candidates

        # Add reviewed_at timestamp if status is being updated
        if "status" in update_data:
            update_data["reviewed_at"] = datetime.now(UTC)

        # Extract UUIDs for the bulk update
        candidate_uuids = [c.uuid for c in candidates]

        # Single bulk UPDATE statement
        stmt = (
            update(MatchCandidate)
            .where(
                MatchCandidate.uuid.in_(candidate_uuids),
                MatchCandidate.deleted_at.is_(None),
            )
            .values(**update_data)
        )
        await self.db.execute(stmt)
        await self.db.commit()

        # Fetch updated candidates in a single query
        select_stmt = select(MatchCandidate).where(
            MatchCandidate.uuid.in_(candidate_uuids),
            MatchCandidate.deleted_at.is_(None),
        )
        result = await self.db.execute(select_stmt)
        return list(result.scalars().all())

    async def get_by_uuids(self, uuids: list[UUID]) -> list[MatchCandidate]:
        """Get multiple candidates by their UUIDs."""
        stmt = select(MatchCandidate).where(
            MatchCandidate.uuid.in_(uuids),
            MatchCandidate.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_task_for_candidate(self, candidate: MatchCandidate) -> Task | None:
        """Get the task for a candidate."""
        stmt = select(Task).where(
            Task.id == candidate.task_id,
            Task.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_task_stats(self, task: Task) -> None:
        """Update task's candidate_count and highest_score."""
        # Count candidates
        count_stmt = select(func.count()).where(
            MatchCandidate.task_id == task.id,
            MatchCandidate.deleted_at.is_(None),
        )
        count_result = await self.db.execute(count_stmt)
        task.candidate_count = count_result.scalar() or 0

        # Get highest score
        max_stmt = select(func.max(MatchCandidate.score)).where(
            MatchCandidate.task_id == task.id,
            MatchCandidate.deleted_at.is_(None),
        )
        max_result = await self.db.execute(max_stmt)
        task.highest_score = max_result.scalar()

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)


def get_candidate_service(db: AsyncSession) -> CandidateService:
    """Factory function for CandidateService."""
    return CandidateService(db)
