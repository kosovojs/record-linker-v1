"""
MatchCandidate model - a potential Wikidata match for a task.

Design notes:
- Same wikidata_id can appear multiple times for same task (different sources)
- status uses CandidateStatus enum for type safety
- source uses CandidateSource enum for type safety
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Column, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import BaseTableModel
from app.schemas.enums import CandidateSource, CandidateStatus
from app.schemas.jsonb_types import (
    CandidateExtraData,
    CandidateMatchedProperties,
    CandidateScoreBreakdown,
)

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

    # Status - using enum for type safety
    status: CandidateStatus = Field(
        default=CandidateStatus.SUGGESTED,
        sa_column=Column(String(50), nullable=False),
    )

    # Matching score
    score: int = Field(
        sa_column=Column(SmallInteger, nullable=False),
        ge=0,
        le=100,
    )

    # Source tracking - using enum for type safety
    source: CandidateSource = Field(
        sa_column=Column(String(50), nullable=False),
    )

    # Typed JSONB - CandidateScoreBreakdown schema
    score_breakdown: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Typed JSONB - CandidateMatchedProperties schema
    matched_properties: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Tags as JSONB list
    tags: list = Field(
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

    # Typed JSONB - CandidateExtraData schema
    extra_data: dict = Field(
        default_factory=lambda: CandidateExtraData().model_dump(),
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Helper methods for typed access
    def get_score_breakdown(self) -> CandidateScoreBreakdown | None:
        """Get score_breakdown as typed Pydantic model."""
        if self.score_breakdown is None:
            return None
        return CandidateScoreBreakdown.model_validate(self.score_breakdown)

    def set_score_breakdown(self, data: CandidateScoreBreakdown) -> None:
        """Set score_breakdown from typed Pydantic model."""
        self.score_breakdown = data.model_dump()

    def get_matched_properties(self) -> CandidateMatchedProperties | None:
        """Get matched_properties as typed Pydantic model."""
        if self.matched_properties is None:
            return None
        return CandidateMatchedProperties.model_validate(self.matched_properties)

    def set_matched_properties(self, data: CandidateMatchedProperties) -> None:
        """Set matched_properties from typed Pydantic model."""
        self.matched_properties = data.model_dump()

    def get_extra_data(self) -> CandidateExtraData:
        """Get extra_data as typed Pydantic model."""
        return CandidateExtraData.model_validate(self.extra_data)

    def set_extra_data(self, data: CandidateExtraData) -> None:
        """Set extra_data from typed Pydantic model."""
        self.extra_data = data.model_dump()
