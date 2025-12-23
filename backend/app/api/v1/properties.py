"""
PropertyDefinition API endpoints.

CRUD operations for property definitions:
- GET /properties - List properties (paginated)
- POST /properties - Create property
- GET /properties/{uuid} - Get property
- PATCH /properties/{uuid} - Update property
- DELETE /properties/{uuid} - Soft delete property
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession, Pagination
from app.api.utils import get_or_404, handle_conflict_error
from app.schemas.common import PaginatedResponse
from app.schemas.property_definition import (
    PropertyDefinitionCreate,
    PropertyDefinitionRead,
    PropertyDefinitionUpdate,
)
from app.services.property_service import PropertyDefinitionService
from app.services.exceptions import ConflictError

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PropertyDefinitionRead])
async def list_properties(
    db: DbSession,
    pagination: Pagination,
    data_type: str | None = Query(default=None, description="Filter by data type"),
    wikidata_only: bool = Query(
        default=False, description="Only properties with Wikidata mapping"
    ),
):
    """List all property definitions with pagination and optional filters."""
    service = PropertyDefinitionService(db)
    items, total = await service.get_list_filtered(
        pagination=pagination,
        data_type=data_type,
        wikidata_only=wikidata_only,
    )

    return PaginatedResponse[PropertyDefinitionRead](
        items=[PropertyDefinitionRead.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_more=(pagination.page * pagination.page_size) < total,
    )


@router.post(
    "", response_model=PropertyDefinitionRead, status_code=status.HTTP_201_CREATED
)
async def create_property(
    db: DbSession,
    data: PropertyDefinitionCreate,
):
    """Create a new property definition."""
    service = PropertyDefinitionService(db)
    try:
        prop = await service.create_with_validation(data)
    except ConflictError as e:
        handle_conflict_error(e)
    return PropertyDefinitionRead.model_validate(prop)


@router.get("/{uuid}", response_model=PropertyDefinitionRead)
async def get_property(
    db: DbSession,
    uuid: UUID,
):
    """Get a single property definition by UUID."""
    service = PropertyDefinitionService(db)
    prop = await get_or_404(service, uuid, "Property definition")
    return PropertyDefinitionRead.model_validate(prop)


@router.patch("/{uuid}", response_model=PropertyDefinitionRead)
async def update_property(
    db: DbSession,
    uuid: UUID,
    data: PropertyDefinitionUpdate,
):
    """Update a property definition."""
    service = PropertyDefinitionService(db)
    prop = await get_or_404(service, uuid, "Property definition")

    try:
        updated = await service.update_with_validation(prop, data)
    except ConflictError as e:
        handle_conflict_error(e)
    return PropertyDefinitionRead.model_validate(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    db: DbSession,
    uuid: UUID,
):
    """Soft delete a property definition."""
    service = PropertyDefinitionService(db)
    prop = await get_or_404(service, uuid, "Property definition")
    await service.soft_delete(prop)
    return None
