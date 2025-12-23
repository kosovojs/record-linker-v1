"""
PropertyDefinition model - defines property types for the EAV pattern.

Design notes:
- Properties are global (shared across datasets) for consistency
- data_type_hint is for UI/validation only - actual values stored as TEXT
- wikidata_property links to Wikidata property IDs for automated matching
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, Index, String, Text, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseTableModel

__all__ = ["PropertyDefinition"]


class PropertyDefinition(BaseTableModel, table=True):
    """
    Defines a property type that can be attached to dataset entries.

    Part of the EAV (Entity-Attribute-Value) pattern:
    - Entity = DatasetEntry
    - Attribute = PropertyDefinition (this model)
    - Value = DatasetEntryProperty
    """

    __tablename__ = "property_definitions"
    __table_args__ = (
        UniqueConstraint("name", name="uq_property_definitions_name"),
        Index("idx_property_definitions_name", "name"),
        Index("idx_property_definitions_data_type", "data_type_hint"),
        Index("idx_property_definitions_wikidata", "wikidata_property"),
    )

    # Identification
    name: str = Field(
        sa_column=Column(String(100), nullable=False),
        max_length=100,
    )
    display_name: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Type hint for client-side handling
    data_type_hint: str = Field(
        default="text",
        sa_column=Column(String(50), nullable=False),
    )

    # Multi-value and display configuration
    is_multivalued: bool = Field(default=False)
    is_searchable: bool = Field(default=True)
    is_display_field: bool = Field(default=False)
    display_order: int = Field(default=0)

    # Wikidata integration
    wikidata_property: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )

    # Optional validation
    validation_regex: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
    )

    # Note: Relationship to values is accessed via queries
