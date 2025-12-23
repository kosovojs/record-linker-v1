"""
DatasetEntry API endpoints.

Entries are nested under datasets:
- GET /datasets/{uuid}/entries - List entries (paginated)
- POST /datasets/{uuid}/entries - Create entries (bulk)
- GET /datasets/{uuid}/entries/{uuid} - Get entry
- PATCH /datasets/{uuid}/entries/{uuid} - Update entry
- DELETE /datasets/{uuid}/entries/{uuid} - Soft delete entry

Plus read-only endpoint for entry properties:
- GET /entries/{uuid}/properties - List properties for entry
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession, Pagination
from app.api.utils import get_or_404, handle_conflict_error
from app.schemas.common import PaginatedResponse
from app.schemas.dataset_entry import DatasetEntryCreate, DatasetEntryRead, DatasetEntryUpdate
from app.services.dataset_service import DatasetService
from app.services.entry_service import EntryService
from app.services.exceptions import ConflictError

router = APIRouter()


async def _enrich_entry_read(service: EntryService, entry) -> DatasetEntryRead:
    """Enrich DatasetEntryRead with dataset_uuid."""
    dataset = await service.get_dataset_for_entry(entry)
    entry_read = DatasetEntryRead.model_validate(entry)
    if dataset:
        entry_read.dataset_uuid = dataset.uuid
    return entry_read


# ============================================================================
# Nested under datasets: /datasets/{dataset_uuid}/entries
# ============================================================================


@router.get(
    "/datasets/{dataset_uuid}/entries",
    response_model=PaginatedResponse[DatasetEntryRead],
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

    entry_reads = [await _enrich_entry_read(entry_service, e) for e in items]

    return PaginatedResponse[DatasetEntryRead](
        items=entry_reads,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_more=(pagination.page * pagination.page_size) < total,
    )


@router.post(
    "/datasets/{dataset_uuid}/entries",
    response_model=list[DatasetEntryRead],
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

    return [await _enrich_entry_read(entry_service, e) for e in entries]


@router.get(
    "/datasets/{dataset_uuid}/entries/{entry_uuid}",
    response_model=DatasetEntryRead,
)
async def get_entry(
    db: DbSession,
    dataset_uuid: UUID,
    entry_uuid: UUID,
):
    """Get a single entry by UUID."""
    # Validate dataset exists
    dataset_service = DatasetService(db)
    await get_or_404(dataset_service, dataset_uuid, "Dataset")

    entry_service = EntryService(db)
    entry = await get_or_404(entry_service, entry_uuid, "Entry")
    return await _enrich_entry_read(entry_service, entry)


@router.patch(
    "/datasets/{dataset_uuid}/entries/{entry_uuid}",
    response_model=DatasetEntryRead,
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
    return await _enrich_entry_read(entry_service, updated)


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
