"""
DatasetEntry request/response schemas for API endpoints.

Patterns:
- DatasetEntryBase: Shared validation for create/update
- DatasetEntryCreate: POST request body
- DatasetEntryUpdate: PATCH request body (all optional)
- DatasetEntryRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.jsonb_types import DatasetEntryExtraData

__all__ = [
    "DatasetEntryBase",
    "DatasetEntryCreate",
    "DatasetEntryUpdate",
    "DatasetEntryRead",
]


class DatasetEntryBase(BaseModel):
    """Shared fields for dataset entry create/update operations."""

    external_id: str = Field(
        min_length=1,
        max_length=255,
        description="ID from the external source (stable identifier)",
    )
    external_url: str | None = Field(
        default=None,
        max_length=500,
        description="Direct URL to this entry in the source system",
    )
    display_name: str | None = Field(
        default=None,
        max_length=500,
        description="Cached display name for UI",
    )


class DatasetEntryCreate(DatasetEntryBase):
    """Schema for creating a new dataset entry."""

    dataset_uuid: UUID = Field(
        description="UUID of the parent dataset",
    )
    raw_data: dict[str, Any] | None = Field(
        default=None,
        description="Original raw data from source",
    )
    extra_data: DatasetEntryExtraData | None = Field(
        default=None,
        description="Additional metadata",
    )


class DatasetEntryUpdate(BaseModel):
    """Schema for updating a dataset entry. All fields optional."""

    external_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="External source ID",
    )
    external_url: str | None = Field(
        default=None,
        max_length=500,
        description="External URL",
    )
    display_name: str | None = Field(
        default=None,
        max_length=500,
        description="Display name",
    )
    raw_data: dict[str, Any] | None = Field(
        default=None,
        description="Raw source data",
    )
    extra_data: DatasetEntryExtraData | None = Field(
        default=None,
        description="Additional metadata",
    )


class DatasetEntryRead(BaseModel):
    """Schema for dataset entry API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    dataset_uuid: UUID | None = Field(
        default=None,
        description="Parent dataset UUID (populated by service layer)",
    )
    external_id: str = Field(description="External source ID")
    external_url: str | None = Field(description="External URL")
    display_name: str | None = Field(description="Display name")
    raw_data: dict[str, Any] | None = Field(description="Raw source data")
    extra_data: dict = Field(description="Additional metadata")
    created_at: datetime = Field(description="When created")
    updated_at: datetime = Field(description="Last update timestamp")
