"""
Project API endpoints.

CRUD operations for projects:
- GET /projects - List projects (paginated)
- POST /projects - Create project
- GET /projects/{uuid} - Get project with stats
- PATCH /projects/{uuid} - Update project
- DELETE /projects/{uuid} - Soft delete project

Workflow endpoints:
- POST /projects/{uuid}/start - Create tasks and activate
- POST /projects/{uuid}/rerun - Reprocess selected tasks
- GET /projects/{uuid}/stats - Detailed statistics
- GET /projects/{uuid}/approved-matches - List approved matches
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import DbSession, Pagination
from app.api.utils import get_or_404, raise_not_found
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService
from app.services.dataset_service import DatasetService
from app.services.exceptions import ValidationError

router = APIRouter()


# ============================================================================
# Workflow request/response schemas
# ============================================================================


class ProjectStartRequest(BaseModel):
    """Request body for starting a project."""
    entry_uuids: list[UUID] | None = Field(
        default=None,
        description="Specific entry UUIDs to create tasks for",
    )
    all_entries: bool = Field(
        default=False,
        description="Create tasks for all entries in dataset",
    )


class ProjectStartResponse(BaseModel):
    """Response for project start."""
    message: str
    tasks_created: int
    project_status: str


class ProjectRerunRequest(BaseModel):
    """Request body for rerunning tasks."""
    criteria: str | None = Field(
        default=None,
        description="Criteria: 'failed', 'no_candidates', 'no_accepted'",
    )
    task_uuids: list[UUID] | None = Field(
        default=None,
        description="Specific task UUIDs to reset",
    )


class ProjectRerunResponse(BaseModel):
    """Response for project rerun."""
    tasks_reset: int


class ProjectStatsResponse(BaseModel):
    """Response for project statistics."""
    total_tasks: int
    by_status: dict[str, int]
    candidates: dict[str, int]
    avg_score: float | None
    progress_percent: float


class ApprovedMatch(BaseModel):
    """Single approved match."""
    task_uuid: str
    entry_external_id: str
    entry_display_name: str | None
    wikidata_id: str
    score: int


class ApprovedMatchesResponse(BaseModel):
    """Response for approved matches."""
    matches: list[ApprovedMatch]
    total: int


# ============================================================================
# CRUD endpoints
# ============================================================================


@router.get("", response_model=PaginatedResponse[ProjectRead])
async def list_projects(
    db: DbSession,
    pagination: Pagination,
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by project status"
    ),
    dataset_uuid: UUID | None = Query(
        default=None, description="Filter by dataset UUID"
    ),
):
    """List all projects with pagination and optional filters."""
    service = ProjectService(db)
    items, total = await service.get_list_with_datasets(
        pagination=pagination,
        status=status_filter,
        dataset_uuid=dataset_uuid,
    )

    return PaginatedResponse[ProjectRead](
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_more=(pagination.page * pagination.page_size) < total,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    db: DbSession,
    data: ProjectCreate,
):
    """Create a new project."""
    dataset_service = DatasetService(db)
    dataset = await dataset_service.get_by_uuid(data.dataset_uuid)
    if not dataset:
        raise_not_found(f"Dataset with UUID '{data.dataset_uuid}'")

    project_service = ProjectService(db)
    project = await project_service.create_with_dataset(data, dataset)

    project_read = ProjectRead.model_validate(project)
    project_read.dataset_uuid = dataset.uuid
    return project_read


@router.get("/{uuid}", response_model=ProjectRead)
async def get_project(
    db: DbSession,
    uuid: UUID,
):
    """Get a single project by UUID with stats."""
    service = ProjectService(db)
    project, dataset = await service.get_with_dataset(uuid)

    if not project:
        raise_not_found("Project")

    project_read = ProjectRead.model_validate(project)
    if dataset:
        project_read.dataset_uuid = dataset.uuid

    return project_read


@router.patch("/{uuid}", response_model=ProjectRead)
async def update_project(
    db: DbSession,
    uuid: UUID,
    data: ProjectUpdate,
):
    """Update a project."""
    service = ProjectService(db)
    project = await get_or_404(service, uuid, "Project")
    updated = await service.update(project, data)

    dataset = await service.get_dataset_for_project(updated)
    project_read = ProjectRead.model_validate(updated)
    if dataset:
        project_read.dataset_uuid = dataset.uuid
    return project_read


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    db: DbSession,
    uuid: UUID,
):
    """Soft delete a project."""
    service = ProjectService(db)
    project = await get_or_404(service, uuid, "Project")
    await service.soft_delete(project)
    return None


# ============================================================================
# Workflow endpoints
# ============================================================================


@router.post("/{uuid}/start", response_model=ProjectStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_project(
    db: DbSession,
    uuid: UUID,
    data: ProjectStartRequest,
):
    """Create tasks for dataset entries and transition project to active."""
    service = ProjectService(db)
    project = await get_or_404(service, uuid, "Project")

    try:
        tasks_created, new_status = await service.start_project(
            project,
            entry_uuids=data.entry_uuids,
            all_entries=data.all_entries,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ProjectStartResponse(
        message="Project started",
        tasks_created=tasks_created,
        project_status=new_status,
    )


@router.post("/{uuid}/rerun", response_model=ProjectRerunResponse, status_code=status.HTTP_202_ACCEPTED)
async def rerun_tasks(
    db: DbSession,
    uuid: UUID,
    data: ProjectRerunRequest,
):
    """Reset specific tasks for reprocessing."""
    service = ProjectService(db)
    project = await get_or_404(service, uuid, "Project")

    try:
        tasks_reset = await service.rerun_tasks(
            project,
            criteria=data.criteria,
            task_uuids=data.task_uuids,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ProjectRerunResponse(tasks_reset=tasks_reset)


@router.get("/{uuid}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    db: DbSession,
    uuid: UUID,
):
    """Get detailed project statistics computed on-the-fly."""
    service = ProjectService(db)
    project = await get_or_404(service, uuid, "Project")

    stats = await service.get_stats(project)
    return ProjectStatsResponse(**stats)


@router.get("/{uuid}/approved-matches", response_model=ApprovedMatchesResponse)
async def get_approved_matches(
    db: DbSession,
    uuid: UUID,
):
    """Get list of approved matches for a project."""
    service = ProjectService(db)
    project = await get_or_404(service, uuid, "Project")

    matches = await service.get_approved_matches(project)
    return ApprovedMatchesResponse(
        matches=[ApprovedMatch(**m) for m in matches],
        total=len(matches),
    )
