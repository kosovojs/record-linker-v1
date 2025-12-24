"""
Task API endpoints.

Tasks are nested under projects:
- GET /projects/{uuid}/tasks - List tasks (paginated)
- POST /projects/{uuid}/tasks - Create task
- GET /projects/{uuid}/tasks/{uuid} - Get task
- PATCH /projects/{uuid}/tasks/{uuid} - Update task
- DELETE /projects/{uuid}/tasks/{uuid} - Soft delete task
- POST /projects/{uuid}/tasks/{uuid}/skip - Skip task

Plus direct alias:
- GET /tasks/{uuid} - Get task by UUID alone
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Path, status
from pydantic import field_validator

from app.api.deps import DbSession, Pagination
from app.api.utils import get_or_404, handle_conflict_error, raise_not_found
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.schemas.validators import parse_json_field
from app.services.entry_service import EntryService
from app.services.exceptions import ConflictError
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter()


# SQLite JSON compatibility
class TaskReadWithValidator(TaskRead):
    """TaskRead with SQLite JSON compatibility."""

    @field_validator("extra_data", mode="before")
    @classmethod
    def parse_extra_data(cls, v):
        return parse_json_field(v)


# ============================================================================
# Nested under projects: /projects/{project_uuid}/tasks
# ============================================================================


@router.get(
    "/projects/{project_uuid}/tasks",
    response_model=PaginatedResponse[TaskReadWithValidator],
)
async def list_tasks(
    db: DbSession,
    pagination: Pagination,
    project_uuid: UUID = Path(
        ...,
        description="The unique identifier of the project",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter tasks by status",
        examples=["pending"],
    ),
    has_candidates: bool | None = Query(
        default=None,
        description="Filter tasks that have at least one candidate",
        examples=[True],
    ),
    has_accepted: bool | None = Query(
        default=None,
        description="Filter tasks that have an accepted candidate",
        examples=[False],
    ),
    min_score: int | None = Query(
        default=None,
        ge=0,
        le=100,
        description="Filter tasks by minimum candidate score",
        examples=[80],
    ),
):
    """List all tasks for a project with filtering."""
    project_service = ProjectService(db)
    project = await get_or_404(project_service, project_uuid, "Project")

    task_service = TaskService(db)
    items, total = await task_service.get_list_for_project(
        project=project,
        pagination=pagination,
        status=status_filter,
        has_candidates=has_candidates,
        has_accepted=has_accepted,
        min_score=min_score,
    )

    # Fixed N+1: use known project_uuid and batch-fetch entry UUIDs
    entry_uuids = await task_service.get_entry_uuids_for_tasks(items)

    task_reads = []
    for task in items:
        task_read = TaskReadWithValidator.model_validate(task)
        task_read.project_uuid = project_uuid  # Known from path
        task_read.dataset_entry_uuid = entry_uuids.get(task.id)
        task_reads.append(task_read)

    return PaginatedResponse[TaskReadWithValidator](
        items=task_reads,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_more=(pagination.page * pagination.page_size) < total,
    )


@router.post(
    "/projects/{project_uuid}/tasks",
    response_model=TaskReadWithValidator,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    db: DbSession,
    data: TaskCreate,
    project_uuid: UUID = Path(
        ...,
        description="The unique identifier of the project",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Create a task for a project."""
    project_service = ProjectService(db)
    project = await get_or_404(project_service, project_uuid, "Project")

    entry_service = EntryService(db)
    entry = await entry_service.get_by_uuid(data.dataset_entry_uuid)
    if not entry:
        raise_not_found(f"Entry with UUID '{data.dataset_entry_uuid}'")

    task_service = TaskService(db)
    try:
        task = await task_service.create_for_project(project, entry, data)
    except ConflictError as e:
        handle_conflict_error(e)

    task_read = TaskReadWithValidator.model_validate(task)
    task_read.project_uuid = project_uuid
    task_read.dataset_entry_uuid = data.dataset_entry_uuid
    return task_read


@router.get(
    "/projects/{project_uuid}/tasks/{task_uuid}",
    response_model=TaskReadWithValidator,
)
async def get_task(
    db: DbSession,
    project_uuid: UUID = Path(
        ...,
        description="The unique identifier of the project",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    task_uuid: UUID = Path(
        ...,
        description="The unique identifier of the task",
        examples=["770e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Get a single task by UUID."""
    project_service = ProjectService(db)
    project = await get_or_404(project_service, project_uuid, "Project")

    task_service = TaskService(db)
    task, entry_uuid = await task_service.get_with_entry_uuid(task_uuid)
    if not task:
        raise_not_found("Task")

    # Verify task belongs to this project
    if task.project_id != project.id:
        raise_not_found("Task")

    task_read = TaskReadWithValidator.model_validate(task)
    task_read.project_uuid = project_uuid
    task_read.dataset_entry_uuid = entry_uuid
    return task_read


@router.patch(
    "/projects/{project_uuid}/tasks/{task_uuid}",
    response_model=TaskReadWithValidator,
)
async def update_task(
    db: DbSession,
    data: TaskUpdate,
    project_uuid: UUID = Path(
        ...,
        description="The unique identifier of the project",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    task_uuid: UUID = Path(
        ...,
        description="The unique identifier of the task",
        examples=["770e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Update a task."""
    project_service = ProjectService(db)
    project = await get_or_404(project_service, project_uuid, "Project")

    task_service = TaskService(db)
    task = await get_or_404(task_service, task_uuid, "Task")

    # Verify task belongs to this project
    if task.project_id != project.id:
        raise_not_found("Task")

    updated = await task_service.update(task, data)

    entry = await task_service.get_entry_for_task(updated)
    task_read = TaskReadWithValidator.model_validate(updated)
    task_read.project_uuid = project_uuid
    task_read.dataset_entry_uuid = entry.uuid if entry else None
    return task_read


@router.delete(
    "/projects/{project_uuid}/tasks/{task_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    db: DbSession,
    project_uuid: UUID = Path(
        ...,
        description="The unique identifier of the project",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    task_uuid: UUID = Path(
        ...,
        description="The unique identifier of the task",
        examples=["770e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Soft delete a task."""
    project_service = ProjectService(db)
    project = await get_or_404(project_service, project_uuid, "Project")

    task_service = TaskService(db)
    task = await get_or_404(task_service, task_uuid, "Task")

    # Verify task belongs to this project
    if task.project_id != project.id:
        raise_not_found("Task")

    await task_service.soft_delete(task)
    return None


@router.post(
    "/projects/{project_uuid}/tasks/{task_uuid}/skip",
    response_model=TaskReadWithValidator,
)
async def skip_task(
    db: DbSession,
    project_uuid: UUID = Path(
        ...,
        description="The unique identifier of the project",
        example="550e8400-e29b-41d4-a716-446655440000",
    ),
    task_uuid: UUID = Path(
        ...,
        description="The unique identifier of the task",
        example="770e8400-e29b-41d4-a716-446655440000",
    ),
):
    """Skip a task."""
    project_service = ProjectService(db)
    project = await get_or_404(project_service, project_uuid, "Project")

    task_service = TaskService(db)
    task = await get_or_404(task_service, task_uuid, "Task")

    # Verify task belongs to this project
    if task.project_id != project.id:
        raise_not_found("Task")

    skipped = await task_service.skip_task(task)

    entry = await task_service.get_entry_for_task(skipped)
    task_read = TaskReadWithValidator.model_validate(skipped)
    task_read.project_uuid = project_uuid
    task_read.dataset_entry_uuid = entry.uuid if entry else None
    return task_read


# ============================================================================
# Direct alias: /tasks/{uuid}
# ============================================================================


@router.get("/tasks/{task_uuid}", response_model=TaskReadWithValidator)
async def get_task_by_uuid(
    db: DbSession,
    task_uuid: UUID = Path(
        ...,
        description="The unique identifier of the task",
        example="770e8400-e29b-41d4-a716-446655440000",
    ),
):
    """Get a task by UUID alone (alias for nested route)."""
    task_service = TaskService(db)
    task, project_uuid, entry_uuid = await task_service.get_with_related_uuids(task_uuid)
    if not task:
        raise_not_found("Task")

    task_read = TaskReadWithValidator.model_validate(task)
    task_read.project_uuid = project_uuid
    task_read.dataset_entry_uuid = entry_uuid
    return task_read
