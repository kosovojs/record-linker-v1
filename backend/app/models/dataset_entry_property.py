"""
DatasetEntryProperty model - stores property values in EAV pattern.

Design notes:
- All values stored as TEXT - type validation at application layer
- value_normalized stores cleaned version for matching
- ordinal supports multi-valued properties (0 = primary)
"""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlmodel import Field

from app.models.base import BaseTableModel

__all__ = ["DatasetEntryProperty"]


class DatasetEntryProperty(BaseTableModel, table=True):
    """
    Stores property values for dataset entries (EAV value table).

    EAV pattern allows each dataset to have different properties
    without schema changes.
    """

    __tablename__ = "dataset_entry_properties"
    __table_args__ = (
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

    # Value storage
    value: str = Field(
        sa_column=Column(Text, nullable=False),
    )
    value_normalized: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Data quality tracking
    confidence: int | None = Field(default=None, ge=0, le=100)
    source: str = Field(
        default="import",
        sa_column=Column(String(50), nullable=False),
    )

    # Multi-value support
    ordinal: int = Field(
        default=0,
        sa_column=Column(SmallInteger, nullable=False),
    )

    # Note: Relationships to dataset_entry and property_definition are accessed via queries
