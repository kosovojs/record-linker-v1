"""
Task model - links a project to a dataset entry for matching.

Design notes:
- Denormalized accepted_wikidata_id allows filtering matched entries
  without joining through candidates table
- highest_score enables sorting by match quality
- unique constraint prevents same entry appearing twice in a project
- reviewed_by_id tracks who made the decision for audit purposes
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Column, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.dataset_entry import DatasetEntry
    from app.models.match_candidate import MatchCandidate
    from app.models.project import Project
    from app.models.user import User

__all__ = ["Task"]


class Task(BaseTableModel, table=True):
    """
    A unit of work: match one dataset entry to Wikidata.

    Each task represents one entry to be reconciled. Tasks can have
    multiple candidates (potential Wikidata matches), and the reviewer
    accepts one or rejects all.
    """

    __tablename__ = "tasks"
    __table_args__ = (
        # Same entry can't be in same project twice
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

    # Status
    status: str = Field(
        default="new",
        sa_column=Column(String(50), nullable=False),
    )

    # Accepted match - denormalized for query performance
    # When a candidate is accepted, we copy its info here to avoid
    # joining through match_candidates for common queries
    accepted_candidate_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("match_candidates.id"), nullable=True),
    )
    accepted_wikidata_id: str | None = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
        description="Accepted QID (e.g., 'Q12345') for quick filtering",
    )

    # Candidate summary - denormalized for list views
    candidate_count: int = Field(
        default=0,
        description="Number of candidates found",
    )
    highest_score: int | None = Field(
        default=None,
        sa_column=Column(SmallInteger, nullable=True),
        ge=0,
        le=100,
        description="Best candidate score for sorting",
    )

    # Processing timestamps
    processing_started_at: datetime | None = Field(default=None)
    processing_completed_at: datetime | None = Field(default=None)

    # Review tracking
    reviewed_at: datetime | None = Field(default=None)
    reviewed_by_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )
    notes: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Reviewer notes about this decision",
    )

    # Error handling
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Error details if status is 'failed'",
    )

    # Processing metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks")
    dataset_entry: Mapped["DatasetEntry"] = relationship(back_populates="tasks")
    reviewed_by: Mapped["User | None"] = relationship()
    candidates: Mapped[list["MatchCandidate"]] = relationship(
        back_populates="task",
        lazy="noload",
        # Don't load accepted_candidate through this to avoid confusion
        foreign_keys="MatchCandidate.task_id",
    )
    accepted_candidate: Mapped["MatchCandidate | None"] = relationship(
        foreign_keys=[accepted_candidate_id],
        lazy="joined",  # Usually want this when loading task
    )
