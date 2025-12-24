"""
Tests for MatchingService.

Tests for name matching, date matching, and composite scoring.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.core.config import MatchingSettings
from app.services.matching_service import (
    CompositeScore,
    DateMatcher,
    MatchScore,
    MatchType,
    NameMatcher,
    ScoreCalculator,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def matching_settings() -> MatchingSettings:
    """Create test matching settings."""
    return MatchingSettings(
        auto_accept_threshold=95,
        high_confidence_threshold=80,
        low_confidence_threshold=50,
        name_weight=0.5,
        date_weight=0.3,
        property_weight=0.2,
        name_exact_score=100,
        name_fuzzy_threshold=70,
        date_exact_score=100,
        date_year_only_score=80,
        date_tolerance_days=3,
    )


@pytest.fixture
def name_matcher(matching_settings: MatchingSettings) -> NameMatcher:
    """Create NameMatcher with test settings."""
    return NameMatcher(settings=matching_settings)


@pytest.fixture
def date_matcher(matching_settings: MatchingSettings) -> DateMatcher:
    """Create DateMatcher with test settings."""
    return DateMatcher(settings=matching_settings)


@pytest.fixture
def score_calculator(matching_settings: MatchingSettings) -> ScoreCalculator:
    """Create ScoreCalculator with test settings."""
    return ScoreCalculator(settings=matching_settings)


# =============================================================================
# Name Matcher Tests
# =============================================================================


class TestNameMatcher:
    """Tests for NameMatcher."""

    def test_exact_match_returns_100(self, name_matcher: NameMatcher):
        """Test exact match returns 100 score."""
        result = name_matcher.compare("Douglas Adams", "Douglas Adams")

        assert result.score == 100
        assert result.match_type == MatchType.NAME
        assert result.details["matched"] == "exact"

    def test_case_insensitive_exact_match(self, name_matcher: NameMatcher):
        """Test case insensitivity."""
        result = name_matcher.compare("DOUGLAS ADAMS", "douglas adams")

        assert result.score == 100
        assert result.details["matched"] == "exact"

    def test_fuzzy_match_high_score(self, name_matcher: NameMatcher):
        """Test fuzzy match for similar names."""
        result = name_matcher.compare("Douglas Noel Adams", "Douglas Adams")

        assert result.score >= 70  # Should be a decent match
        assert result.details["matched"] == "fuzzy"

    def test_fuzzy_match_low_score(self, name_matcher: NameMatcher):
        """Test fuzzy match for dissimilar names."""
        result = name_matcher.compare("John Smith", "Douglas Adams")

        assert result.score < 50  # Should be a poor match

    def test_alias_exact_match(self, name_matcher: NameMatcher):
        """Test exact match against alias."""
        result = name_matcher.compare("DNA", "Douglas Adams", aliases=["DNA", "D.N. Adams"])

        assert result.score == 100
        assert result.details["matched"] == "exact"
        assert result.details["against"] == "alias"

    def test_alias_fuzzy_match(self, name_matcher: NameMatcher):
        """Test fuzzy match picks best alias."""
        result = name_matcher.compare(
            "Douglas N Adams",
            "Douglas Noel Adams - English Author",
            aliases=["Douglas N. Adams", "DNA"],
        )

        assert result.score >= 90  # Should match well with alias

    def test_empty_name_returns_zero(self, name_matcher: NameMatcher):
        """Test empty name returns zero score."""
        result = name_matcher.compare("", "Douglas Adams")
        assert result.score == 0

        result = name_matcher.compare("Douglas Adams", "")
        assert result.score == 0

    def test_word_order_differences(self, name_matcher: NameMatcher):
        """Test token set ratio handles word order."""
        result = name_matcher.compare("Adams, Douglas", "Douglas Adams")

        assert result.score >= 80  # Token set should handle this well


# =============================================================================
# Date Matcher Tests
# =============================================================================


class TestDateMatcher:
    """Tests for DateMatcher."""

    def test_exact_date_match(self, date_matcher: DateMatcher):
        """Test exact date match returns 100."""
        result = date_matcher.compare(date(1952, 3, 11), date(1952, 3, 11))

        assert result.score == 100
        assert result.details["matched"] == "exact"

    def test_exact_date_from_strings(self, date_matcher: DateMatcher):
        """Test date parsing from strings."""
        result = date_matcher.compare("1952-03-11", "1952-03-11")

        assert result.score == 100

    def test_close_date_within_tolerance(self, date_matcher: DateMatcher):
        """Test close dates within tolerance get high score."""
        result = date_matcher.compare(date(1952, 3, 11), date(1952, 3, 12))

        assert result.score >= 80
        assert result.details["matched"] == "close"

    def test_year_only_match(self, date_matcher: DateMatcher):
        """Test year-only match gets year score."""
        result = date_matcher.compare(date(1952, 3, 11), date(1952, 7, 15))

        assert result.score == 80
        assert result.details["matched"] == "year_only"

    def test_different_year_no_match(self, date_matcher: DateMatcher):
        """Test different years return zero score."""
        result = date_matcher.compare(date(1952, 3, 11), date(1960, 3, 11))

        assert result.score == 0
        assert result.details["matched"] == "none"

    def test_missing_date_returns_zero(self, date_matcher: DateMatcher):
        """Test missing date returns zero."""
        result = date_matcher.compare(None, date(1952, 3, 11))
        assert result.score == 0

        result = date_matcher.compare(date(1952, 3, 11), None)
        assert result.score == 0

    def test_wikidata_datetime_format(self, date_matcher: DateMatcher):
        """Test Wikidata datetime format parsing."""
        # Wikidata uses ISO format with timezone
        result = date_matcher.compare("1952-03-11", "1952-03-11T00:00:00Z")

        assert result.score == 100

    def test_year_only_string(self, date_matcher: DateMatcher):
        """Test year-only string parsing."""
        result = date_matcher.compare("1952", "1952-03-11")

        assert result.score == 80  # Year match


# =============================================================================
# Score Calculator Tests
# =============================================================================


class TestScoreCalculator:
    """Tests for ScoreCalculator."""

    def test_high_confidence_match(self, score_calculator: ScoreCalculator):
        """Test high confidence match with name and date."""
        entry_data = {
            "name": "Douglas Adams",
            "dob": "1952-03-11",
        }
        wikidata_entity = {
            "label": "Douglas Adams",
            "aliases": ["DNA"],
            "claims": {
                "P569": [{"mainsnak": {"datavalue": {"value": {"time": "+1952-03-11T00:00:00Z"}}}}]
            },
        }

        result = score_calculator.calculate(entry_data, wikidata_entity)

        assert result.total_score >= 90
        assert result.confidence == "high"
        assert "name" in result.matched_fields

    def test_medium_confidence_name_only(self, score_calculator: ScoreCalculator):
        """Test medium confidence with name match only."""
        entry_data = {"name": "Douglas Adams"}
        wikidata_entity = {"label": "Douglas Adams", "aliases": []}

        result = score_calculator.calculate(entry_data, wikidata_entity)

        assert result.total_score == 100  # Only name, weighted to 100
        # Single field high match should still be high confidence since score > 80
        assert result.confidence in ("high", "medium")

    def test_low_score_match(self, score_calculator: ScoreCalculator):
        """Test low score for poor match."""
        entry_data = {"name": "John Smith", "dob": "1980-01-01"}
        wikidata_entity = {
            "label": "Douglas Adams",
            "claims": {
                "P569": [{"mainsnak": {"datavalue": {"value": {"time": "+1952-03-11T00:00:00Z"}}}}]
            },
        }

        result = score_calculator.calculate(entry_data, wikidata_entity)

        assert result.total_score < 50
        assert result.confidence == "low"

    def test_empty_data_returns_zero(self, score_calculator: ScoreCalculator):
        """Test empty data returns zero score."""
        result = score_calculator.calculate({}, {})

        assert result.total_score == 0
        assert result.confidence == "none"

    def test_uses_display_name_fallback(self, score_calculator: ScoreCalculator):
        """Test falls back to display_name if name not present."""
        entry_data = {"display_name": "Douglas Adams"}
        wikidata_entity = {"label": "Douglas Adams"}

        result = score_calculator.calculate(entry_data, wikidata_entity)

        assert result.total_score == 100

    def test_composite_score_includes_all_scores(self, score_calculator: ScoreCalculator):
        """Test composite score includes individual scores."""
        entry_data = {"name": "Douglas Adams", "dob": "1952-03-11"}
        wikidata_entity = {
            "label": "Douglas Adams",
            "claims": {
                "P569": [{"mainsnak": {"datavalue": {"value": {"time": "+1952-03-11T00:00:00Z"}}}}]
            },
        }

        result = score_calculator.calculate(entry_data, wikidata_entity)

        assert len(result.scores) == 2
        score_types = [s.match_type for s in result.scores]
        assert MatchType.NAME in score_types
        assert MatchType.DATE in score_types


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for matching."""

    def test_unicode_names(self, name_matcher: NameMatcher):
        """Test unicode character handling."""
        result = name_matcher.compare("Jürgen Müller", "Jurgen Muller")

        # Should still get a reasonable fuzzy match
        assert result.score >= 70

    def test_names_with_titles(self, name_matcher: NameMatcher):
        """Test names with titles/honorifics."""
        result = name_matcher.compare("Dr. Douglas Adams", "Douglas Adams")

        assert result.score >= 80

    def test_very_long_names(self, name_matcher: NameMatcher):
        """Test very long name strings."""
        long_name = "Douglas Noel Adams, English Author and Screenwriter"
        result = name_matcher.compare(long_name, "Douglas Adams")

        assert result.score >= 50  # Partial match should work

    def test_invalid_date_format(self, date_matcher: DateMatcher):
        """Test invalid date format handling."""
        result = date_matcher.compare("not-a-date", "1952-03-11")

        assert result.score == 0
        assert result.details["reason"] == "invalid_date_format"
