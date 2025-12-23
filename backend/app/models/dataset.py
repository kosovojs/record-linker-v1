"""
Dataset model - represents an external data source (e.g., EliteProspects).

Design notes:
- slug provides URL-friendly identifier for API routes
- entry_count is denormalized for performance - avoids COUNT(*) on large tables
- metadata JSONB stores source-specific info that varies per dataset
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.dataset_entry import DatasetEntry
    from app.models.project import Project

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
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Source information
    source_url: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
    )
    source_type: str = Field(
        default="web_scrape",
        sa_column=Column(String(50), nullable=False),
    )
    entity_type: str = Field(
        sa_column=Column(String(100), nullable=False),
    )

    # Denormalized count - updated when entries are added/removed
    entry_count: int = Field(default=0)

    # Sync tracking
    last_synced_at: Optional[datetime] = Field(default=None)

    # Flexible extra data - varies by source (version, license, contact, etc.)
    extra_data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    entries: List["DatasetEntry"] = Relationship(back_populates="dataset")
    projects: List["Project"] = Relationship(back_populates="dataset")
