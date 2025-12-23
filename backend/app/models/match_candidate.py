"""
MatchCandidate model - a potential Wikidata match for a task.

Design notes:
- Same wikidata_id can appear multiple times for same task (different sources)
  This is intentional - keeps full audit trail of how candidates were found
- score_breakdown stores per-property scores for debugging
- matched_properties shows which fields contributed to the match
- tags ARRAY allows flexible categorization without separate table
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Column, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User

__all__ = ["MatchCandidate"]


class MatchCandidate(BaseTableModel, table=True):
    """
    A potential Wikidata match for a task.

    Multiple candidates can exist per task, representing different
    potential matches with varying confidence levels. Reviewers
    accept one or reject all.
    """

    __tablename__ = "match_candidates"
    __table_args__ = (
        Index("idx_mc_task", "task_id"),
        Index("idx_mc_task_status", "task_id", "status"),
        Index("idx_mc_wikidata", "wikidata_id"),
        Index("idx_mc_status", "status"),
        Index("idx_mc_score", "score"),
        Index("idx_mc_source", "source"),
        Index("idx_mc_reviewed_by", "reviewed_by_id"),
        # GIN index for array containment queries on tags
        # Index("idx_mc_tags", "tags", postgresql_using="gin"),
    )

    # Parent task
    task_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tasks.id"), nullable=False),
    )

    # Wikidata reference - just the QID, no cached data
    # We fetch current Wikidata info at display time to stay fresh
    wikidata_id: str = Field(
        sa_column=Column(String(20), nullable=False),
        max_length=20,
        description="Wikidata item ID (e.g., 'Q12345')",
    )

    # Status
    status: str = Field(
        default="suggested",
        sa_column=Column(String(50), nullable=False),
    )

    # Matching score
    score: int = Field(
        sa_column=Column(SmallInteger, nullable=False),
        ge=0,
        le=100,
        description="Match confidence 0-100",
    )

    # Source tracking - how was this candidate found?
    source: str = Field(
        sa_column=Column(String(50), nullable=False),
        description="How found: automated_search, manual, file_import, ai_suggestion",
    )

    # Detailed scoring breakdown for transparency
    # Shows score per property: {"name_similarity": 85, "date_match": 100, ...}
    score_breakdown: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Evidence for the match - which properties matched
    # {"P569": {"source": "1990-05-15", "wikidata": "1990-05-15", "match": true}}
    matched_properties: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Tags for flexible categorization
    # Using JSONB list instead of ARRAY for SQLModel compatibility
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )

    # Notes
    notes: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Review tracking
    reviewed_at: datetime | None = Field(default=None)
    reviewed_by_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )

    # Additional metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        back_populates="candidates",
        foreign_keys=[task_id],
    )
    reviewed_by: Mapped["User | None"] = relationship()
