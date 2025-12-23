"""
DatasetEntry API endpoints.

Entries are nested under datasets:
- GET /datasets/{uuid}/entries - List entries (paginated)
- POST /datasets/{uuid}/entries - Create entries (bulk)
- GET /datasets/{uuid}/entries/{uuid} - Get entry
- PATCH /datasets/{uuid}/entries/{uuid} - Update entry
- DELETE /datasets/{uuid}/entries/{uuid} - Soft delete entry
"""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import field_validator

from app.api.deps import DbSession, Pagination
from app.api.utils import get_or_404, handle_conflict_error
from app.schemas.common import PaginatedResponse
from app.schemas.dataset_entry import DatasetEntryCreate, DatasetEntryRead, DatasetEntryUpdate
from app.services.dataset_service import DatasetService
from app.services.entry_service import EntryService
from app.services.exceptions import ConflictError

router = APIRouter()


# SQLite JSON compatibility for extra_data/raw_data fields
class DatasetEntryReadWithValidator(DatasetEntryRead):
    """DatasetEntryRead with SQLite JSON compatibility."""

    @field_validator("extra_data", "raw_data", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if v is None:
            return {} if cls.model_fields.get("extra_data") else None
        if isinstance(v, str):
            return json.loads(v)
        return v


# ============================================================================
# Nested under datasets: /datasets/{dataset_uuid}/entries
# ============================================================================


@router.get(
    "/datasets/{dataset_uuid}/entries",
    response_model=PaginatedResponse[DatasetEntryReadWithValidator],
)
async def list_entries(
    db: DbSession,
    dataset_uuid: UUID,
    pagination: Pagination,
    search: str | None = Query(default=None, description="Search in display_name"),
):
    """List all entries for a dataset with pagination."""
    dataset_service = DatasetService(db)
    dataset = await get_or_404(dataset_service, dataset_uuid, "Dataset")

    entry_service = EntryService(db)
    items, total = await entry_service.get_list_for_dataset(
        dataset=dataset,
        pagination=pagination,
        search=search,
    )

    # No N+1: we already know dataset_uuid from the path parameter
    entry_reads = []
    for entry in items:
        entry_read = DatasetEntryReadWithValidator.model_validate(entry)
        entry_read.dataset_uuid = dataset_uuid  # Use known value, no extra query
        entry_reads.append(entry_read)

    return PaginatedResponse[DatasetEntryReadWithValidator](
        items=entry_reads,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_more=(pagination.page * pagination.page_size) < total,
    )


@router.post(
    "/datasets/{dataset_uuid}/entries",
    response_model=list[DatasetEntryReadWithValidator],
    status_code=status.HTTP_201_CREATED,
)
async def create_entries(
    db: DbSession,
    dataset_uuid: UUID,
    data: list[DatasetEntryCreate],
):
    """Create entries for a dataset (bulk, all-or-nothing)."""
    dataset_service = DatasetService(db)
    dataset = await get_or_404(dataset_service, dataset_uuid, "Dataset")

    entry_service = EntryService(db)
    try:
        entries = await entry_service.bulk_create_for_dataset(dataset, data)
    except ConflictError as e:
        handle_conflict_error(e)

    # Use known dataset_uuid - no N+1
    entry_reads = []
    for entry in entries:
        entry_read = DatasetEntryReadWithValidator.model_validate(entry)
        entry_read.dataset_uuid = dataset_uuid
        entry_reads.append(entry_read)
    return entry_reads


@router.get(
    "/datasets/{dataset_uuid}/entries/{entry_uuid}",
    response_model=DatasetEntryReadWithValidator,
)
async def get_entry(
    db: DbSession,
    dataset_uuid: UUID,
    entry_uuid: UUID,
):
    """Get a single entry by UUID."""
    dataset_service = DatasetService(db)
    await get_or_404(dataset_service, dataset_uuid, "Dataset")

    entry_service = EntryService(db)
    entry = await get_or_404(entry_service, entry_uuid, "Entry")

    entry_read = DatasetEntryReadWithValidator.model_validate(entry)
    entry_read.dataset_uuid = dataset_uuid
    return entry_read


@router.patch(
    "/datasets/{dataset_uuid}/entries/{entry_uuid}",
    response_model=DatasetEntryReadWithValidator,
)
async def update_entry(
    db: DbSession,
    dataset_uuid: UUID,
    entry_uuid: UUID,
    data: DatasetEntryUpdate,
):
    """Update an entry."""
    dataset_service = DatasetService(db)
    await get_or_404(dataset_service, dataset_uuid, "Dataset")

    entry_service = EntryService(db)
    entry = await get_or_404(entry_service, entry_uuid, "Entry")

    try:
        updated = await entry_service.update_with_validation(entry, data)
    except ConflictError as e:
        handle_conflict_error(e)

    entry_read = DatasetEntryReadWithValidator.model_validate(updated)
    entry_read.dataset_uuid = dataset_uuid
    return entry_read


@router.delete(
    "/datasets/{dataset_uuid}/entries/{entry_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_entry(
    db: DbSession,
    dataset_uuid: UUID,
    entry_uuid: UUID,
):
    """Soft delete an entry."""
    dataset_service = DatasetService(db)
    await get_or_404(dataset_service, dataset_uuid, "Dataset")

    entry_service = EntryService(db)
    entry = await get_or_404(entry_service, entry_uuid, "Entry")
    await entry_service.soft_delete(entry)
    return None
