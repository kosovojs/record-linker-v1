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

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession, Pagination
from app.schemas.common import PaginatedResponse
from app.schemas.dataset import DatasetCreate, DatasetRead, DatasetUpdate
from app.services.dataset_service import DatasetService
from app.services.exceptions import ConflictError

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DatasetRead])
async def list_datasets(
    db: DbSession,
    pagination: Pagination,
    source_type: str | None = Query(default=None, description="Filter by source type"),
    entity_type: str | None = Query(default=None, description="Filter by entity type"),
    search: str | None = Query(default=None, description="Search in name/description"),
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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    return DatasetRead.model_validate(dataset)


@router.get("/{uuid}", response_model=DatasetRead)
async def get_dataset(
    db: DbSession,
    uuid: UUID,
):
    """Get a single dataset by UUID."""
    service = DatasetService(db)
    dataset = await service.get_by_uuid(uuid)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return DatasetRead.model_validate(dataset)


@router.patch("/{uuid}", response_model=DatasetRead)
async def update_dataset(
    db: DbSession,
    uuid: UUID,
    data: DatasetUpdate,
):
    """Update a dataset."""
    service = DatasetService(db)
    dataset = await service.get_by_uuid(uuid)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    try:
        updated = await service.update_with_validation(dataset, data)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    return DatasetRead.model_validate(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    db: DbSession,
    uuid: UUID,
):
    """Soft delete a dataset."""
    service = DatasetService(db)
    dataset = await service.get_by_uuid(uuid)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    await service.soft_delete(dataset)
    return None
