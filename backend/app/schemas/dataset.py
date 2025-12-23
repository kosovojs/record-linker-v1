"""
Dataset request/response schemas for API endpoints.

Patterns:
- DatasetBase: Shared validation for create/update
- DatasetCreate: POST request body
- DatasetUpdate: PATCH request body (all optional)
- DatasetRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.enums import DatasetSourceType
from app.schemas.jsonb_types import DatasetExtraData

__all__ = [
    "DatasetBase",
    "DatasetCreate",
    "DatasetUpdate",
    "DatasetRead",
]


class DatasetBase(BaseModel):
    """Shared fields for dataset create/update operations."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable dataset name",
    )
    slug: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-friendly identifier (lowercase, hyphens allowed)",
    )
    description: str | None = Field(
        default=None,
        description="Detailed description of the dataset",
    )
    source_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL to the external source",
    )
    source_type: DatasetSourceType = Field(
        default=DatasetSourceType.WEB_SCRAPE,
        description="How data was obtained",
    )
    entity_type: str = Field(
        min_length=1,
        max_length=100,
        description="Type of entities (e.g., 'person', 'organization')",
    )


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset."""

    extra_data: DatasetExtraData | None = Field(
        default=None,
        description="Additional metadata (uses defaults if not provided)",
    )


class DatasetUpdate(BaseModel):
    """Schema for updating an existing dataset. All fields optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Dataset name",
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-friendly identifier",
    )
    description: str | None = Field(
        default=None,
        description="Dataset description",
    )
    source_url: str | None = Field(
        default=None,
        max_length=500,
        description="Source URL",
    )
    source_type: DatasetSourceType | None = Field(
        default=None,
        description="How data was obtained",
    )
    entity_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Entity type",
    )
    extra_data: DatasetExtraData | None = Field(
        default=None,
        description="Additional metadata",
    )


class DatasetRead(BaseModel):
    """Schema for dataset API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    name: str = Field(description="Dataset name")
    slug: str = Field(description="URL-friendly identifier")
    description: str | None = Field(description="Dataset description")
    source_url: str | None = Field(description="Source URL")
    source_type: DatasetSourceType = Field(description="How data was obtained")
    entity_type: str = Field(description="Type of entities")
    entry_count: int = Field(description="Number of entries in dataset")
    last_synced_at: datetime | None = Field(description="Last sync timestamp")
    extra_data: dict = Field(description="Additional metadata")
    created_at: datetime = Field(description="When dataset was created")
    updated_at: datetime = Field(description="Last update timestamp")
