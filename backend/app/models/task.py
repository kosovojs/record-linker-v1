"""
Task model - links a project to a dataset entry for matching.

Design notes:
- Denormalized accepted_wikidata_id for quick filtering
- highest_score enables sorting by match quality
- status uses TaskStatus enum for type safety
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import BaseTableModel
from app.schemas.enums import TaskStatus
from app.schemas.jsonb_types import TaskExtraData

__all__ = ["Task"]


class Task(BaseTableModel, table=True):
    """
    A unit of work: match one dataset entry to Wikidata.
    """

    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("project_id", "dataset_entry_id", name="uq_tasks_project_entry"),
        Index("idx_tasks_project", "project_id"),
        Index("idx_tasks_entry", "dataset_entry_id"),
        Index("idx_tasks_project_status", "project_id", "status"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_accepted_wikidata", "accepted_wikidata_id"),
        Index("idx_tasks_highest_score", "highest_score"),
        Index("idx_tasks_reviewed_by", "reviewed_by_id"),
    )

    # Foreign keys
    project_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("projects.id"), nullable=False),
    )
    dataset_entry_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("dataset_entries.id"), nullable=False),
    )

    # Status - using enum for type safety
    status: TaskStatus = Field(
        default=TaskStatus.NEW,
        sa_column=Column(String(50), nullable=False),
    )

    # Accepted match - denormalized
    # use_alter=True breaks circular FK dependency with match_candidates table
    accepted_candidate_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("match_candidates.id", use_alter=True),
            nullable=True,
        ),
    )
    accepted_wikidata_id: str | None = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )

    # Candidate summary
    candidate_count: int = Field(default=0)
    highest_score: int | None = Field(
        default=None,
        sa_column=Column(SmallInteger, nullable=True),
        ge=0,
        le=100,
    )

    # Processing timestamps
    processing_started_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
    )
    processing_completed_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
    )

    # Review tracking
    reviewed_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
    )
    reviewed_by_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )
    notes: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Error handling
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Typed JSONB - use TaskExtraData schema
    extra_data: dict = Field(
        default_factory=lambda: TaskExtraData().model_dump(),
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Helper methods for typed access
    def get_extra_data(self) -> TaskExtraData:
        """Get extra_data as typed Pydantic model."""
        return TaskExtraData.model_validate(self.extra_data)

    def set_extra_data(self, data: TaskExtraData) -> None:
        """Set extra_data from typed Pydantic model."""
        self.extra_data = data.model_dump()
