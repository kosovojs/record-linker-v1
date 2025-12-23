"""
DatasetEntryProperty request/response schemas for API endpoints.

Patterns:
- DatasetEntryPropertyBase: Shared validation for create/update
- DatasetEntryPropertyCreate: POST request body
- DatasetEntryPropertyUpdate: PATCH request body (all optional)
- DatasetEntryPropertyRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import PropertyValueSource

__all__ = [
    "DatasetEntryPropertyBase",
    "DatasetEntryPropertyCreate",
    "DatasetEntryPropertyUpdate",
    "DatasetEntryPropertyRead",
]


class DatasetEntryPropertyBase(BaseModel):
    """Shared fields for dataset entry property create/update operations."""

    value: str = Field(
        min_length=1,
        description="The property value (stored as text)",
    )
    value_normalized: str | None = Field(
        default=None,
        description="Normalized/cleaned version for matching",
    )
    confidence: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Confidence score for extracted values (0-100)",
    )
    source: PropertyValueSource = Field(
        default=PropertyValueSource.IMPORT,
        description="How this value was obtained",
    )
    ordinal: int = Field(
        default=0,
        ge=0,
        description="Order within multi-valued properties (0 = primary)",
    )


class DatasetEntryPropertyCreate(DatasetEntryPropertyBase):
    """Schema for creating a new dataset entry property."""

    dataset_entry_uuid: UUID = Field(
        description="UUID of the parent dataset entry",
    )
    property_uuid: UUID = Field(
        description="UUID of the property definition",
    )


class DatasetEntryPropertyUpdate(BaseModel):
    """Schema for updating a dataset entry property. All fields optional."""

    value: str | None = Field(
        default=None,
        min_length=1,
        description="Property value",
    )
    value_normalized: str | None = Field(
        default=None,
        description="Normalized value",
    )
    confidence: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Confidence score",
    )
    source: PropertyValueSource | None = Field(
        default=None,
        description="Value source",
    )
    ordinal: int | None = Field(
        default=None,
        ge=0,
        description="Ordinal position",
    )


class DatasetEntryPropertyRead(BaseModel):
    """Schema for dataset entry property API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    dataset_entry_uuid: UUID | None = Field(
        default=None,
        description="Parent entry UUID (populated by service layer)",
    )
    property_uuid: UUID | None = Field(
        default=None,
        description="Property definition UUID (populated by service layer)",
    )
    value: str = Field(description="Property value")
    value_normalized: str | None = Field(description="Normalized value")
    confidence: int | None = Field(description="Confidence score")
    source: str = Field(description="Value source")
    ordinal: int = Field(description="Ordinal position")
    created_at: datetime = Field(description="When created")
    updated_at: datetime = Field(description="Last update timestamp")
