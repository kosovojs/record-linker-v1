"""
Dataset API endpoints.

CRUD operations for datasets:
- GET /datasets - List datasets (paginated)
- POST /datasets - Create dataset
- GET /datasets/{uuid} - Get dataset
- PATCH /datasets/{uuid} - Update dataset
- DELETE /datasets/{uuid} - Soft delete dataset
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Path, status

from app.api.deps import DbSession, Pagination
from app.api.utils import get_or_404, handle_conflict_error
from app.schemas.common import PaginatedResponse
from app.schemas.dataset import DatasetCreate, DatasetRead, DatasetUpdate
from app.services.dataset_service import DatasetService
from app.services.exceptions import ConflictError

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DatasetRead])
async def list_datasets(
    db: DbSession,
    pagination: Pagination,
    source_type: str | None = Query(
        default=None,
        description="Filter datasets by source type (e.g., wikidata, csv)",
        examples=["wikidata"],
    ),
    entity_type: str | None = Query(
        default=None,
        description="Filter datasets by entity type (e.g., human, city)",
        examples=["human"],
    ),
    search: str | None = Query(
        default=None,
        description="Search in dataset name or description",
        examples=["population"],
    ),
):
    """List all datasets with pagination and optional filters."""
    service = DatasetService(db)
    items, total = await service.get_list_filtered(
        pagination=pagination,
        source_type=source_type,
        entity_type=entity_type,
        search=search,
    )

    return PaginatedResponse[DatasetRead](
        items=[DatasetRead.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_more=(pagination.page * pagination.page_size) < total,
    )


@router.post("", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    db: DbSession,
    data: DatasetCreate,
):
    """Create a new dataset."""
    service = DatasetService(db)
    try:
        dataset = await service.create_with_validation(data)
    except ConflictError as e:
        handle_conflict_error(e)
    return DatasetRead.model_validate(dataset)


@router.get("/{uuid}", response_model=DatasetRead)
async def get_dataset(
    db: DbSession,
    uuid: UUID = Path(
        ...,
        description="The unique identifier of the dataset",
        examples=["440e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Get a single dataset by UUID."""
    service = DatasetService(db)
    dataset = await get_or_404(service, uuid, "Dataset")
    return DatasetRead.model_validate(dataset)


@router.patch("/{uuid}", response_model=DatasetRead)
async def update_dataset(
    db: DbSession,
    data: DatasetUpdate,
    uuid: UUID = Path(
        ...,
        description="The unique identifier of the dataset",
        examples=["440e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Update a dataset."""
    service = DatasetService(db)
    dataset = await get_or_404(service, uuid, "Dataset")

    try:
        updated = await service.update_with_validation(dataset, data)
    except ConflictError as e:
        handle_conflict_error(e)
    return DatasetRead.model_validate(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    db: DbSession,
    uuid: UUID = Path(
        ...,
        description="The unique identifier of the dataset",
        examples=["440e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Soft delete a dataset."""
    service = DatasetService(db)
    dataset = await get_or_404(service, uuid, "Dataset")
    await service.soft_delete(dataset)
    return None
