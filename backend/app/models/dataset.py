"""
Dataset model - represents an external data source (e.g., EliteProspects).

Design notes:
- slug provides URL-friendly identifier for API routes
- entry_count is denormalized for performance - avoids COUNT(*) on large tables
- source_type uses DatasetSourceType enum for type safety
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import BaseTableModel
from app.schemas.enums import DatasetSourceType
from app.schemas.jsonb_types import DatasetExtraData

__all__ = ["Dataset"]


class Dataset(BaseTableModel, table=True):
    """
    An external data source containing entity profiles to be matched.

    Examples: EliteProspects players, Olympedia athletes, IMDB actors.
    One source may have multiple datasets (e.g., players vs coaches).
    """

    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_datasets_slug"),
        Index("idx_datasets_slug", "slug"),
        Index("idx_datasets_entity_type", "entity_type"),
        Index("idx_datasets_source_type", "source_type"),
    )

    # Identification
    name: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
    )
    slug: str = Field(
        sa_column=Column(String(100), nullable=False),
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Source information - using enum for type safety
    source_url: str | None = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
    )
    source_type: DatasetSourceType = Field(
        default=DatasetSourceType.WEB_SCRAPE,
        sa_column=Column(String(50), nullable=False),
    )
    entity_type: str = Field(
        sa_column=Column(String(100), nullable=False),
    )

    # Denormalized count - updated when entries are added/removed
    entry_count: int = Field(default=0)

    # Sync tracking
    last_synced_at: datetime | None = Field(default=None)

    # Typed JSONB - use DatasetExtraData schema
    extra_data: dict = Field(
        default_factory=lambda: DatasetExtraData().model_dump(),
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Helper methods for typed access
    def get_extra_data(self) -> DatasetExtraData:
        """Get extra_data as typed Pydantic model."""
        return DatasetExtraData.model_validate(self.extra_data)

    def set_extra_data(self, data: DatasetExtraData) -> None:
        """Set extra_data from typed Pydantic model."""
        self.extra_data = data.model_dump()
