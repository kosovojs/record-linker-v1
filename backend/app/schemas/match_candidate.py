"""
MatchCandidate request/response schemas for API endpoints.

Patterns:
- MatchCandidateBase: Shared validation for create/update
- MatchCandidateCreate: POST request body
- MatchCandidateUpdate: PATCH request body (all optional)
- MatchCandidateRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import CandidateSource, CandidateStatus
from app.schemas.jsonb_types import (
    CandidateExtraData,
    CandidateMatchedProperties,
    CandidateScoreBreakdown,
)

__all__ = [
    "MatchCandidateBase",
    "MatchCandidateCreate",
    "MatchCandidateUpdate",
    "MatchCandidateRead",
]


class MatchCandidateBase(BaseModel):
    """Shared fields for match candidate create/update operations."""

    wikidata_id: str = Field(
        min_length=2,
        max_length=20,
        pattern=r"^Q\d+$",
        description="Wikidata item ID (e.g., 'Q12345')",
    )
    score: int = Field(
        ge=0,
        le=100,
        description="Match confidence score (0-100)",
    )
    source: CandidateSource = Field(
        description="How this candidate was found",
    )
    notes: str | None = Field(
        default=None,
        description="Notes about this candidate",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="User-defined tags for filtering",
    )


class MatchCandidateCreate(MatchCandidateBase):
    """Schema for creating a new match candidate."""

    task_uuid: UUID | None = Field(
        default=None,
        description="UUID of the parent task (can be omitted if provided in URL path)",
    )
    score_breakdown: CandidateScoreBreakdown | None = Field(
        default=None,
        description="Detailed scoring breakdown",
    )
    matched_properties: CandidateMatchedProperties | None = Field(
        default=None,
        description="Property comparison details",
    )
    extra_data: CandidateExtraData | None = Field(
        default=None,
        description="Additional metadata",
    )


class MatchCandidateUpdate(BaseModel):
    """Schema for updating a match candidate. All fields optional."""

    status: CandidateStatus | None = Field(
        default=None,
        description="Candidate status",
    )
    notes: str | None = Field(
        default=None,
        description="Notes",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags",
    )


class MatchCandidateRead(BaseModel):
    """Schema for match candidate API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    task_uuid: UUID | None = Field(
        default=None,
        description="Parent task UUID (populated by service layer)",
    )
    wikidata_id: str = Field(description="Wikidata item ID")
    status: CandidateStatus = Field(description="Candidate status")
    score: int = Field(description="Match confidence score")
    source: CandidateSource = Field(description="How candidate was found")
    score_breakdown: dict | None = Field(description="Scoring breakdown")
    matched_properties: dict | None = Field(description="Property comparisons")
    tags: list[str] = Field(description="Tags")
    notes: str | None = Field(description="Notes")
    reviewed_at: datetime | None = Field(description="Review timestamp")
    reviewed_by_uuid: UUID | None = Field(
        default=None,
        description="Reviewer UUID (populated by service layer)",
    )
    extra_data: dict = Field(description="Additional metadata")
    created_at: datetime = Field(description="When created")
    updated_at: datetime = Field(description="Last update timestamp")
