"""
DatasetEntry model - individual records from an external dataset.

Design notes:
- external_id is the stable ID from the source system
- display_name is denormalized for efficient list views
- raw_data stores the original import data for debugging
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Column, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.dataset_entry_property import DatasetEntryProperty
    from app.models.task import Task

__all__ = ["DatasetEntry"]


class DatasetEntry(BaseTableModel, table=True):
    """
    An individual record from an external dataset (e.g., one person profile).

    Properties are stored separately in DatasetEntryProperty (EAV pattern)
    for schema flexibility - different sources have different fields.
    """

    __tablename__ = "dataset_entries"
    __table_args__ = (
        UniqueConstraint("dataset_id", "external_id", name="uq_dataset_entries_external"),
        Index("idx_dataset_entries_dataset", "dataset_id"),
        Index("idx_dataset_entries_external_id", "dataset_id", "external_id"),
        Index("idx_dataset_entries_display_name", "display_name"),
    )

    # Parent dataset
    dataset_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("datasets.id"), nullable=False),
    )

    # External source identification
    external_id: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
    )
    external_url: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
    )

    # Denormalized display name for efficient list rendering
    display_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
    )

    # Original data - kept for debugging
    raw_data: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Import extra data
    extra_data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    dataset: "Dataset" = Relationship(back_populates="entries")
    properties: List["DatasetEntryProperty"] = Relationship(back_populates="dataset_entry")
    tasks: List["Task"] = Relationship(back_populates="dataset_entry")
