"""
Task model - links a project to a dataset entry for matching.

Design notes:
- Denormalized accepted_wikidata_id for quick filtering
- highest_score enables sorting by match quality
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Column, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

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

    # Status
    status: str = Field(
        default="new",
        sa_column=Column(String(50), nullable=False),
    )

    # Accepted match - denormalized
    accepted_candidate_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("match_candidates.id"), nullable=True),
    )
    accepted_wikidata_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
    )

    # Candidate summary
    candidate_count: int = Field(default=0)
    highest_score: Optional[int] = Field(
        default=None,
        sa_column=Column(SmallInteger, nullable=True),
        ge=0,
        le=100,
    )

    # Processing timestamps
    processing_started_at: Optional[datetime] = Field(default=None)
    processing_completed_at: Optional[datetime] = Field(default=None)

    # Review tracking
    reviewed_at: Optional[datetime] = Field(default=None)
    reviewed_by_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )
    notes: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Extra data
    extra_data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    project: "Project" = Relationship(back_populates="tasks")
    dataset_entry: "DatasetEntry" = Relationship(back_populates="tasks")
    candidates: List["MatchCandidate"] = Relationship(back_populates="task")
    # Note: accepted_candidate relationship needs sa_relationship_kwargs for non-default FK
    # reviewed_by: "User" = Relationship() - omitted to avoid complexity
