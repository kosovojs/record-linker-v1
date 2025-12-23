"""
Project API endpoints.

CRUD operations for projects:
- GET /projects - List projects (paginated)
- POST /projects - Create project
- GET /projects/{uuid} - Get project with stats
- PATCH /projects/{uuid} - Update project
- DELETE /projects/{uuid} - Soft delete project
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession, Pagination
from app.api.utils import get_or_404, raise_not_found
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService
from app.services.dataset_service import DatasetService

router = APIRouter()


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
