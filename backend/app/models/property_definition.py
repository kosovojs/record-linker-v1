"""
PropertyDefinition model - defines property types for the EAV pattern.

Design notes:
- Properties are global (shared across datasets) for consistency
- data_type_hint is for UI/validation only - actual values stored as TEXT
- wikidata_property links to Wikidata property IDs for automated matching
- is_multivalued allows properties like "nationality" to have multiple values
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.dataset_entry_property import DatasetEntryProperty

__all__ = ["PropertyDefinition"]


class PropertyDefinition(BaseTableModel, table=True):
    """
    Defines a property type that can be attached to dataset entries.

    Part of the Entity-Attribute-Value (EAV) pattern:
    - Entity = DatasetEntry
    - Attribute = PropertyDefinition (this model)
    - Value = DatasetEntryProperty

    Global properties allow consistent matching across different datasets
    (e.g., "date_of_birth" means the same thing in EliteProspects and Olympedia).
    """

    __tablename__ = "property_definitions"
    __table_args__ = (
        UniqueConstraint("name", name="uq_property_definitions_name"),
        Index("idx_property_definitions_name", "name"),
        Index("idx_property_definitions_data_type", "data_type_hint"),
        Index("idx_property_definitions_wikidata", "wikidata_property"),
    )

    # Identification - machine-readable name for code, display_name for UI
    name: str = Field(
        sa_column=Column(String(100), nullable=False),
        max_length=100,
        description="Machine-readable name (e.g., 'date_of_birth', 'full_name')",
    )
    display_name: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
        description="Human-readable label (e.g., 'Date of Birth', 'Full Name')",
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Type hint for client-side handling
    # All values are stored as TEXT in DB - this guides UI rendering
    data_type_hint: str = Field(
        default="text",
        sa_column=Column(String(50), nullable=False),
        description="Hint for UI: text, date, number, url, email, identifier",
    )

    # Multi-value support - some properties need multiple values
    # e.g., person may have multiple nationalities, names, etc.
    is_multivalued: bool = Field(
        default=False,
        description="Whether multiple values are allowed for this property",
    )

    # Display configuration
    is_searchable: bool = Field(
        default=True,
        description="Include in search indexes for full-text search",
    )
    is_display_field: bool = Field(
        default=False,
        description="Show in summary views (typically name, title fields)",
    )
    display_order: int = Field(
        default=0,
        description="Order for UI display (lower = first)",
    )

    # Wikidata integration - P569 for DOB, P27 for country, etc.
    # Enables automated property matching during candidate comparison
    wikidata_property: str | None = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
        description="Corresponding Wikidata property ID (e.g., 'P569')",
    )

    # Optional validation
    validation_regex: str | None = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
        description="Optional regex for value validation",
    )

    # Relationships
    values: Mapped[list["DatasetEntryProperty"]] = relationship(
        back_populates="property_definition",
        lazy="noload",
    )
