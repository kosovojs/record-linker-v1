"""
Dataset model - represents an external data source (e.g., EliteProspects).

Design notes:
- slug provides URL-friendly identifier for API routes
- entry_count is denormalized for performance - avoids COUNT(*) on large tables
- metadata JSONB stores source-specific info that varies per dataset
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

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
        description="Human-readable name (e.g., 'EliteProspects - Players')",
    )
    slug: str = Field(
        sa_column=Column(String(100), nullable=False),
        max_length=100,
        description="URL-friendly identifier (e.g., 'eliteprospects-players')",
    )

    # Description
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Source information
    source_url: str | None = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
        description="URL to the external source website",
    )
    source_type: str = Field(
        default="web_scrape",
        sa_column=Column(String(50), nullable=False),
        description="How data was obtained: web_scrape, api, file_import, manual",
    )
    entity_type: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="Type of entities: person, organization, location, etc.",
    )

    # Denormalized count - updated when entries are added/removed
    # Avoids expensive COUNT(*) queries on potentially millions of entries
    entry_count: int = Field(
        default=0,
        description="Cached count of entries for quick access",
    )

    # Sync tracking
    last_synced_at: datetime | None = Field(
        default=None,
        description="Last time data was refreshed from source",
    )

    # Flexible metadata - varies by source (version, license, contact, etc.)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    entries: Mapped[list["DatasetEntry"]] = relationship(
        back_populates="dataset",
        lazy="noload",
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="dataset",
        lazy="noload",
    )
