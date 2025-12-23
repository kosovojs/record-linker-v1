"""Tests for MatchCandidate request/response schemas."""

from uuid import uuid4
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.match_candidate import (
    MatchCandidateBase,
    MatchCandidateCreate,
    MatchCandidateUpdate,
    MatchCandidateRead,
)
from app.schemas.enums import CandidateSource, CandidateStatus
from app.schemas.jsonb_types import CandidateScoreBreakdown, CandidateMatchedProperties


class TestMatchCandidateBase:
    """Tests for MatchCandidateBase schema."""

    def test_valid_base(self):
        """Test creating valid MatchCandidateBase."""
        candidate = MatchCandidateBase(
            wikidata_id="Q12345",
            score=85,
            source=CandidateSource.AUTOMATED_SEARCH,
        )
        assert candidate.wikidata_id == "Q12345"
        assert candidate.score == 85
        assert candidate.tags == []

    def test_wikidata_id_pattern(self):
        """Test Wikidata ID must have Q prefix."""
        with pytest.raises(ValidationError):
            MatchCandidateBase(
                wikidata_id="P123",  # Wrong prefix
                score=50,
                source=CandidateSource.MANUAL,
            )

    def test_score_range(self):
        """Test score must be 0-100."""
        # Valid range
        candidate = MatchCandidateBase(
            wikidata_id="Q1",
            score=0,
            source=CandidateSource.MANUAL,
        )
        assert candidate.score == 0

        candidate = MatchCandidateBase(
            wikidata_id="Q1",
            score=100,
            source=CandidateSource.MANUAL,
        )
        assert candidate.score == 100

        # Out of range
        with pytest.raises(ValidationError):
            MatchCandidateBase(
                wikidata_id="Q1",
                score=150,
                source=CandidateSource.MANUAL,
            )


class TestMatchCandidateCreate:
    """Tests for MatchCandidateCreate schema."""

    def test_valid_create_minimal(self):
        """Test creating with minimal fields."""
        candidate = MatchCandidateCreate(
            task_uuid=uuid4(),
            wikidata_id="Q12345",
            score=75,
            source=CandidateSource.AUTOMATED_SEARCH,
        )
        assert candidate.score_breakdown is None
        assert candidate.matched_properties is None

    def test_valid_create_full(self):
        """Test creating with all fields."""
        candidate = MatchCandidateCreate(
            task_uuid=uuid4(),
            wikidata_id="Q67890",
            score=90,
            source=CandidateSource.AI_SUGGESTION,
            notes="High confidence match",
            tags=["high_confidence", "exact_name_match"],
            score_breakdown=CandidateScoreBreakdown(),
            matched_properties=CandidateMatchedProperties(),
        )
        assert len(candidate.tags) == 2


class TestMatchCandidateUpdate:
    """Tests for MatchCandidateUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid."""
        update = MatchCandidateUpdate()
        assert update.status is None

    def test_status_update(self):
        """Test status update."""
        update = MatchCandidateUpdate(status=CandidateStatus.ACCEPTED)
        assert update.status == CandidateStatus.ACCEPTED

    def test_tags_update(self):
        """Test tags update."""
        update = MatchCandidateUpdate(tags=["reviewed", "verified"])
        assert len(update.tags) == 2


class TestMatchCandidateRead:
    """Tests for MatchCandidateRead schema."""

    def test_valid_read(self):
        """Test creating MatchCandidateRead."""
        now = datetime.utcnow()
        candidate = MatchCandidateRead(
            uuid=uuid4(),
            task_uuid=uuid4(),
            wikidata_id="Q12345",
            status=CandidateStatus.SUGGESTED,
            score=85,
            source=CandidateSource.AUTOMATED_SEARCH,
            score_breakdown=None,
            matched_properties=None,
            tags=[],
            notes=None,
            reviewed_at=None,
            reviewed_by_uuid=None,
            extra_data={},
            created_at=now,
            updated_at=now,
        )
        assert candidate.wikidata_id == "Q12345"
        assert candidate.status == CandidateStatus.SUGGESTED
