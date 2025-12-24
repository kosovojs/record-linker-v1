"""
Candidate API endpoints.

Candidates are nested under tasks:
- GET /tasks/{uuid}/candidates - List candidates (not paginated)
- POST /tasks/{uuid}/candidates - Create candidates (bulk)
- GET /tasks/{uuid}/candidates/{uuid} - Get candidate
- PATCH /tasks/{uuid}/candidates/{uuid} - Update candidate
- DELETE /tasks/{uuid}/candidates/{uuid} - Soft delete candidate
- POST /tasks/{uuid}/candidates/{uuid}/accept - Accept candidate
- POST /tasks/{uuid}/candidates/{uuid}/reject - Reject candidate
- PATCH /tasks/{uuid}/candidates/bulk - Bulk update
"""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.api.deps import DbSession
from app.api.utils import get_or_404
from app.schemas.match_candidate import (
    MatchCandidateCreate,
    MatchCandidateRead,
    MatchCandidateUpdate,
)
from app.schemas.task import TaskRead
from app.services.candidate_service import CandidateService
from app.services.exceptions import ValidationError
from app.services.task_service import TaskService

router = APIRouter()


# SQLite JSON compatibility
class MatchCandidateReadWithValidator(MatchCandidateRead):
    """MatchCandidateRead with SQLite JSON compatibility."""

    @field_validator("score_breakdown", "matched_properties", mode="before")
    @classmethod
    def parse_nullable_json_fields(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("extra_data", mode="before")
    @classmethod
    def parse_extra_data(cls, v):
        if v is None:
            return {}
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        from app.schemas.enums import CandidateStatus
        if isinstance(v, str):
            return CandidateStatus(v)
        return v

    @field_validator("source", mode="before")
    @classmethod
    def parse_source(cls, v):
        from app.schemas.enums import CandidateSource
        if isinstance(v, str):
            return CandidateSource(v)
        return v


class TaskReadWithValidator(TaskRead):
    """TaskRead with SQLite JSON compatibility."""

    @field_validator("extra_data", mode="before")
    @classmethod
    def parse_extra_data(cls, v):
        if v is None:
            return {}
        if isinstance(v, str):
            return json.loads(v)
        return v


# Request/response schemas for special endpoints
class BulkCandidateCreate(BaseModel):
    """Schema for bulk candidate creation."""
    candidates: list[MatchCandidateCreate] = Field(
        min_length=1,
        description="List of candidates to create",
    )


class BulkCandidateUpdateRequest(BaseModel):
    """Schema for bulk candidate update."""
    candidate_uuids: list[UUID] = Field(
        min_length=1,
        description="UUIDs of candidates to update",
    )
    updates: MatchCandidateUpdate = Field(
        description="Updates to apply to all candidates",
    )


class AcceptRejectResponse(BaseModel):
    """Response for accept/reject actions."""
    task: TaskReadWithValidator
    candidate: MatchCandidateReadWithValidator


# ============================================================================
# Nested under tasks: /tasks/{task_uuid}/candidates
# ============================================================================


@router.get(
    "/tasks/{task_uuid}/candidates",
    response_model=list[MatchCandidateReadWithValidator],
)
async def list_candidates(
    db: DbSession,
    task_uuid: UUID,
):
    """List all candidates for a task (not paginated per spec)."""
    task_service = TaskService(db)
    task = await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)
    items = await candidate_service.get_list_for_task(task)

    # Populate task_uuid for all candidates
    return [
        MatchCandidateReadWithValidator(
            **candidate.model_dump(),
            task_uuid=task_uuid,
        )
        for candidate in items
    ]


@router.post(
    "/tasks/{task_uuid}/candidates",
    response_model=list[MatchCandidateReadWithValidator],
    status_code=status.HTTP_201_CREATED,
)
async def create_candidates_bulk(
    db: DbSession,
    task_uuid: UUID,
    data: BulkCandidateCreate,
):
    """Create candidates for a task (bulk, all-or-nothing)."""
    task_service = TaskService(db)
    task = await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)
    created = await candidate_service.create_bulk(task, data.candidates)

    return [
        MatchCandidateReadWithValidator(
            **candidate.model_dump(),
            task_uuid=task_uuid,
        )
        for candidate in created
    ]


@router.patch(
    "/tasks/{task_uuid}/candidates/bulk",
    response_model=list[MatchCandidateReadWithValidator],
)
async def bulk_update_candidates(
    db: DbSession,
    task_uuid: UUID,
    data: BulkCandidateUpdateRequest,
):
    """Bulk update candidates."""
    task_service = TaskService(db)
    await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)

    # Fetch all candidates by UUID
    candidates = await candidate_service.get_by_uuids(data.candidate_uuids)

    if len(candidates) != len(data.candidate_uuids):
        found_uuids = {c.uuid for c in candidates}
        missing = [str(u) for u in data.candidate_uuids if u not in found_uuids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidates not found: {', '.join(missing)}",
        )

    updated = await candidate_service.bulk_update(candidates, data.updates)

    return [
        MatchCandidateReadWithValidator(
            **candidate.model_dump(),
            task_uuid=task_uuid,
        )
        for candidate in updated
    ]


@router.get(
    "/tasks/{task_uuid}/candidates/{candidate_uuid}",
    response_model=MatchCandidateReadWithValidator,
)
async def get_candidate(
    db: DbSession,
    task_uuid: UUID,
    candidate_uuid: UUID,
):
    """Get a single candidate by UUID."""
    task_service = TaskService(db)
    await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)
    candidate = await get_or_404(candidate_service, candidate_uuid, "Candidate")

    result = MatchCandidateReadWithValidator.model_validate(candidate)
    result.task_uuid = task_uuid
    return result


@router.patch(
    "/tasks/{task_uuid}/candidates/{candidate_uuid}",
    response_model=MatchCandidateReadWithValidator,
)
async def update_candidate(
    db: DbSession,
    task_uuid: UUID,
    candidate_uuid: UUID,
    data: MatchCandidateUpdate,
):
    """Update a candidate."""
    task_service = TaskService(db)
    await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)
    candidate = await get_or_404(candidate_service, candidate_uuid, "Candidate")
    updated = await candidate_service.update(candidate, data)

    result = MatchCandidateReadWithValidator.model_validate(updated)
    result.task_uuid = task_uuid
    return result


@router.delete(
    "/tasks/{task_uuid}/candidates/{candidate_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_candidate(
    db: DbSession,
    task_uuid: UUID,
    candidate_uuid: UUID,
):
    """Soft delete a candidate."""
    task_service = TaskService(db)
    await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)
    candidate = await get_or_404(candidate_service, candidate_uuid, "Candidate")
    await candidate_service.soft_delete(candidate)
    return None


@router.post(
    "/tasks/{task_uuid}/candidates/{candidate_uuid}/accept",
    response_model=AcceptRejectResponse,
)
async def accept_candidate(
    db: DbSession,
    task_uuid: UUID,
    candidate_uuid: UUID,
):
    """Accept a candidate, updating task status to reviewed."""
    task_service = TaskService(db)
    task = await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)
    candidate = await get_or_404(candidate_service, candidate_uuid, "Candidate")

    try:
        updated_candidate, updated_task = await candidate_service.accept_candidate(
            candidate, task
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return AcceptRejectResponse(
        task=TaskReadWithValidator(
            **updated_task.model_dump(),
            project_uuid=None,  # Would need to fetch project
            dataset_entry_uuid=None,  # Would need to fetch entry
        ),
        candidate=MatchCandidateReadWithValidator(
            **updated_candidate.model_dump(),
            task_uuid=task_uuid,
        ),
    )


@router.post(
    "/tasks/{task_uuid}/candidates/{candidate_uuid}/reject",
    response_model=MatchCandidateReadWithValidator,
)
async def reject_candidate(
    db: DbSession,
    task_uuid: UUID,
    candidate_uuid: UUID,
):
    """Reject a candidate."""
    task_service = TaskService(db)
    await get_or_404(task_service, task_uuid, "Task")

    candidate_service = CandidateService(db)
    candidate = await get_or_404(candidate_service, candidate_uuid, "Candidate")

    try:
        updated = await candidate_service.reject_candidate(candidate)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    result = MatchCandidateReadWithValidator.model_validate(updated)
    result.task_uuid = task_uuid
    return result
