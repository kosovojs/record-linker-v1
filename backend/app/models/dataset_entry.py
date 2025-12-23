"""
DatasetEntry model - individual records from an external dataset.

Design notes:
- external_id is the stable ID from the source system (never our generated ID)
- display_name is denormalized for efficient list views without joining properties
- raw_data stores the original import data for debugging/reprocessing
- unique constraint on (dataset_id, external_id) prevents duplicate imports
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Column, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

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
        # Prevent duplicate imports from same source
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
        description="Stable ID from the source system",
    )
    external_url: str | None = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
        description="Direct link to this record in the source system",
    )

    # Denormalized display name for efficient list rendering
    # Updated from properties (e.g., full_name) after import
    display_name: str | None = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
        description="Cached name for UI (avoids property join)",
    )

    # Original data - kept for debugging and potential reprocessing
    # Not used for matching - use properties instead
    raw_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Import metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="entries")
    properties: Mapped[list["DatasetEntryProperty"]] = relationship(
        back_populates="dataset_entry",
        lazy="noload",
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="dataset_entry",
        lazy="noload",
    )
