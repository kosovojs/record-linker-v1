"""
PropertyDefinition request/response schemas for API endpoints.

Patterns:
- PropertyDefinitionBase: Shared validation for create/update
- PropertyDefinitionCreate: POST request body
- PropertyDefinitionUpdate: PATCH request body (all optional)
- PropertyDefinitionRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import PropertyDataType

__all__ = [
    "PropertyDefinitionBase",
    "PropertyDefinitionCreate",
    "PropertyDefinitionUpdate",
    "PropertyDefinitionRead",
]


class PropertyDefinitionBase(BaseModel):
    """Shared fields for property definition create/update operations."""

    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Machine-readable name (e.g., 'date_of_birth')",
    )
    display_name: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable label (e.g., 'Date of Birth')",
    )
    description: str | None = Field(
        default=None,
        description="Explanation of what this property represents",
    )
    data_type_hint: PropertyDataType = Field(
        default=PropertyDataType.TEXT,
        description="Hint for UI rendering and validation",
    )
    is_multivalued: bool = Field(
        default=False,
        description="Whether multiple values are allowed",
    )
    is_searchable: bool = Field(
        default=True,
        description="Whether to index for search",
    )
    is_display_field: bool = Field(
        default=False,
        description="Whether to show in summary views",
    )
    display_order: int = Field(
        default=0,
        ge=0,
        description="Order for display (lower = first)",
    )


class PropertyDefinitionCreate(PropertyDefinitionBase):
    """Schema for creating a new property definition."""

    wikidata_property: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^P\d+$",
        description="Wikidata property ID (e.g., 'P569' for DOB)",
    )
    validation_regex: str | None = Field(
        default=None,
        max_length=500,
        description="Optional regex for value validation",
    )


class PropertyDefinitionUpdate(BaseModel):
    """Schema for updating a property definition. All fields optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Machine-readable name",
    )
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Human-readable label",
    )
    description: str | None = Field(
        default=None,
        description="Property description",
    )
    data_type_hint: PropertyDataType | None = Field(
        default=None,
        description="Data type hint",
    )
    is_multivalued: bool | None = Field(
        default=None,
        description="Allow multiple values",
    )
    is_searchable: bool | None = Field(
        default=None,
        description="Index for search",
    )
    is_display_field: bool | None = Field(
        default=None,
        description="Show in summary views",
    )
    display_order: int | None = Field(
        default=None,
        ge=0,
        description="Display order",
    )
    wikidata_property: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^P\d+$",
        description="Wikidata property ID",
    )
    validation_regex: str | None = Field(
        default=None,
        max_length=500,
        description="Validation regex",
    )


class PropertyDefinitionRead(BaseModel):
    """Schema for property definition API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    name: str = Field(description="Machine-readable name")
    display_name: str = Field(description="Human-readable label")
    description: str | None = Field(description="Property description")
    data_type_hint: str = Field(description="Data type hint")
    is_multivalued: bool = Field(description="Allows multiple values")
    is_searchable: bool = Field(description="Indexed for search")
    is_display_field: bool = Field(description="Shown in summary views")
    display_order: int = Field(description="Display order")
    wikidata_property: str | None = Field(description="Wikidata property ID")
    validation_regex: str | None = Field(description="Validation regex")
    created_at: datetime = Field(description="When created")
    updated_at: datetime = Field(description="Last update timestamp")
