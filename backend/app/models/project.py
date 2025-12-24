"""
Project model - top-level reconciliation work unit.

Design notes:
- One project = one dataset
- Denormalized task counts avoid expensive aggregation queries
- status uses ProjectStatus enum for type safety
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import BaseTableModel
from app.schemas.enums import ProjectStatus
from app.schemas.jsonb_types import ProjectConfig

__all__ = ["Project"]


class Project(BaseTableModel, table=True):
    """
    A reconciliation project for matching dataset entries to Wikidata.
    """

    __tablename__ = "projects"
    __table_args__ = (
        Index("idx_projects_dataset", "dataset_id"),
        Index("idx_projects_owner", "owner_id"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_created", "created_at"),
    )

    # Foreign keys
    dataset_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("datasets.id"), nullable=False),
    )
    owner_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )

    # Identification
    name: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Status - using enum for type safety
    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT,
        sa_column=Column(String(50), nullable=False),
    )

    # Denormalized counts
    task_count: int = Field(default=0)
    tasks_completed: int = Field(default=0)
    tasks_with_candidates: int = Field(default=0)

    # Typed JSONB - use ProjectConfig schema
    config: dict = Field(
        default_factory=lambda: ProjectConfig().model_dump(),
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Timing
    started_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
    )

    # Helper methods for typed access
    def get_config(self) -> ProjectConfig:
        """Get config as typed Pydantic model."""
        return ProjectConfig.model_validate(self.config)

    def set_config(self, config: ProjectConfig) -> None:
        """Set config from typed Pydantic model."""
        self.config = config.model_dump()
