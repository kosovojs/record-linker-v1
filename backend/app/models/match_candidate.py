"""
MatchCandidate model - a potential Wikidata match for a task.

Design notes:
- Same wikidata_id can appear multiple times for same task (different sources)
- score_breakdown stores per-property scores
- tags stored as JSONB list for SQLModel compatibility
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.task import Task

__all__ = ["MatchCandidate"]


class MatchCandidate(BaseTableModel, table=True):
    """
    A potential Wikidata match for a task.
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
    )

    # Parent task
    task_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("tasks.id"), nullable=False),
    )

    # Wikidata reference
    wikidata_id: str = Field(
        sa_column=Column(String(20), nullable=False),
        max_length=20,
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
    )

    # Source tracking
    source: str = Field(
        sa_column=Column(String(50), nullable=False),
    )

    # Detailed scoring
    score_breakdown: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    matched_properties: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Tags as JSONB list
    tags: list = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )

    # Notes
    notes: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Review tracking
    reviewed_at: Optional[datetime] = Field(default=None)
    reviewed_by_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )

    # Extra data
    extra_data: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships
    task: "Task" = Relationship(back_populates="candidates")
