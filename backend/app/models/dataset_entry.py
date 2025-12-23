"""
DatasetEntry model - individual records from an external dataset.

Design notes:
- external_id is the stable ID from the source system
- display_name is denormalized for efficient list views
- extra_data uses DatasetEntryExtraData typed schema
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Column, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import BaseTableModel
from app.schemas.jsonb_types import DatasetEntryExtraData

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

    # Original data - kept for debugging (no typed schema, truly raw)
    raw_data: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Typed JSONB - use DatasetEntryExtraData schema
    extra_data: dict = Field(
        default_factory=lambda: DatasetEntryExtraData().model_dump(),
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Helper methods for typed access
    def get_extra_data(self) -> DatasetEntryExtraData:
        """Get extra_data as typed Pydantic model."""
        return DatasetEntryExtraData.model_validate(self.extra_data)

    def set_extra_data(self, data: DatasetEntryExtraData) -> None:
        """Set extra_data from typed Pydantic model."""
        self.extra_data = data.model_dump()
