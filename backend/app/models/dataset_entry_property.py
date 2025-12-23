"""
DatasetEntryProperty model - stores property values in EAV pattern.

Design notes:
- All values stored as TEXT - type validation happens at application layer
- value_normalized stores cleaned version for matching (lowercase, no diacritics)
- ordinal supports multi-valued properties (0 = primary, 1+ = additional)
- source tracks how value was obtained for data quality assessment
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Column, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.dataset_entry import DatasetEntry
    from app.models.property_definition import PropertyDefinition

__all__ = ["DatasetEntryProperty"]


class DatasetEntryProperty(BaseTableModel, table=True):
    """
    Stores property values for dataset entries (EAV value table).

    EAV (Entity-Attribute-Value) pattern allows each dataset to have
    different properties without schema changes. Trade-off: more complex
    queries but maximum flexibility for heterogeneous data sources.
    """

    __tablename__ = "dataset_entry_properties"
    __table_args__ = (
        # Unique per entry+property+ordinal to allow multi-valued properties
        UniqueConstraint(
            "dataset_entry_id", "property_id", "ordinal",
            name="uq_dep_entry_property_ordinal"
        ),
        Index("idx_dep_entry", "dataset_entry_id"),
        Index("idx_dep_property", "property_id"),
        Index("idx_dep_entry_property", "dataset_entry_id", "property_id"),
        Index("idx_dep_value_normalized", "value_normalized"),
    )

    # Foreign keys
    dataset_entry_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("dataset_entries.id"), nullable=False),
    )
    property_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("property_definitions.id"), nullable=False),
    )

    # Value storage - always TEXT for simplicity and flexibility
    value: str = Field(
        sa_column=Column(Text, nullable=False),
        description="The property value",
    )
    # Normalized for matching: lowercase, diacritics removed, whitespace normalized
    # Pre-computed to avoid runtime normalization during search
    value_normalized: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Cleaned value for matching (lowercase, no diacritics)",
    )

    # Data quality tracking
    confidence: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Extraction confidence 0-100, null for manual data",
    )
    source: str = Field(
        default="import",
        sa_column=Column(String(50), nullable=False),
        description="How value was obtained: import, manual, derived, api",
    )

    # Multi-value support: ordinal 0 = primary, 1+ = additional values
    # E.g., person with multiple nationalities or names
    ordinal: int = Field(
        default=0,
        sa_column=Column(SmallInteger, nullable=False),
        description="Order for multi-valued props (0 = primary)",
    )

    # Relationships
    dataset_entry: Mapped["DatasetEntry"] = relationship(back_populates="properties")
    property_definition: Mapped["PropertyDefinition"] = relationship(back_populates="values")
