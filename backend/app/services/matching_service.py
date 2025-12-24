"""
Matching and scoring service for comparing dataset entries with Wikidata entities.

Provides configurable scoring algorithms for:
- Name matching (fuzzy with rapidfuzz)
- Date matching (with tolerance)
- Property matching (exact and fuzzy)
- Composite weighted scoring
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from rapidfuzz import fuzz

from app.core.config import MatchingSettings, get_settings

logger = logging.getLogger(__name__)


class MatchType(StrEnum):
    """Types of matches that can be computed."""

    NAME = "name"
    DATE = "date"
    PROPERTY = "property"


@dataclass
class MatchScore:
    """Result of a single match comparison."""

    match_type: MatchType
    score: int  # 0-100
    weight: float  # Weight for composite scoring
    details: dict[str, Any] | None = None


@dataclass
class CompositeScore:
    """Result of composite matching across multiple criteria."""

    total_score: int  # 0-100 weighted average
    scores: list[MatchScore]
    confidence: str  # "high", "medium", "low", "none"
    matched_fields: list[str]


# =============================================================================
# Name Matcher
# =============================================================================


class NameMatcher:
    """
    Fuzzy name matching using rapidfuzz.

    Supports multiple comparison strategies:
    - Exact match (100)
    - Token set ratio (handles word order differences)
    - Partial ratio (handles substrings)
    - Simple ratio (character-level similarity)
    """

    def __init__(self, settings: MatchingSettings | None = None):
        self.settings = settings or get_settings().matching

    def compare(
        self,
        entry_name: str,
        wikidata_label: str,
        aliases: list[str] | None = None,
    ) -> MatchScore:
        """
        Compare entry name against Wikidata label and aliases.

        Args:
            entry_name: Name from the dataset entry
            wikidata_label: Primary label from Wikidata
            aliases: Optional list of Wikidata aliases

        Returns:
            MatchScore with best match score
        """
        if not entry_name or not wikidata_label:
            return MatchScore(
                match_type=MatchType.NAME,
                score=0,
                weight=self.settings.name_weight,
                details={"reason": "missing_name"},
            )

        entry_normalized = self._normalize(entry_name)
        label_normalized = self._normalize(wikidata_label)

        # Try exact match first
        if entry_normalized == label_normalized:
            return MatchScore(
                match_type=MatchType.NAME,
                score=self.settings.name_exact_score,
                weight=self.settings.name_weight,
                details={"matched": "exact", "against": "label"},
            )

        # Compute fuzzy scores against label
        best_score = self._best_fuzzy_score(entry_normalized, label_normalized)
        best_match = "label"

        # Try aliases if provided
        if aliases:
            for alias in aliases:
                alias_normalized = self._normalize(alias)
                if entry_normalized == alias_normalized:
                    return MatchScore(
                        match_type=MatchType.NAME,
                        score=self.settings.name_exact_score,
                        weight=self.settings.name_weight,
                        details={"matched": "exact", "against": "alias", "alias": alias},
                    )

                alias_score = self._best_fuzzy_score(entry_normalized, alias_normalized)
                if alias_score > best_score:
                    best_score = alias_score
                    best_match = f"alias:{alias}"

        return MatchScore(
            match_type=MatchType.NAME,
            score=best_score,
            weight=self.settings.name_weight,
            details={"matched": "fuzzy", "against": best_match, "fuzzy_score": best_score},
        )

    def _normalize(self, name: str) -> str:
        """Normalize name for comparison."""
        return name.strip().lower()

    def _best_fuzzy_score(self, s1: str, s2: str) -> int:
        """Get best fuzzy match score using multiple strategies."""
        scores = [
            fuzz.ratio(s1, s2),
            fuzz.token_set_ratio(s1, s2),
            fuzz.partial_ratio(s1, s2),
        ]
        return int(max(scores))


# =============================================================================
# Date Matcher
# =============================================================================


class DateMatcher:
    """
    Date matching with configurable tolerance.

    Supports:
    - Exact date match
    - Year-only match
    - Close match (within tolerance days)
    """

    def __init__(self, settings: MatchingSettings | None = None):
        self.settings = settings or get_settings().matching

    def compare(
        self,
        entry_date: date | str | None,
        wikidata_date: date | str | None,
    ) -> MatchScore:
        """
        Compare dates from entry and Wikidata.

        Args:
            entry_date: Date from dataset entry (date object or ISO string)
            wikidata_date: Date from Wikidata (date object or ISO string, may be partial)

        Returns:
            MatchScore with match result
        """
        if entry_date is None or wikidata_date is None:
            return MatchScore(
                match_type=MatchType.DATE,
                score=0,
                weight=self.settings.date_weight,
                details={"reason": "missing_date"},
            )

        # Parse dates if strings
        entry_parsed = self._parse_date(entry_date)
        wikidata_parsed = self._parse_date(wikidata_date)

        if entry_parsed is None or wikidata_parsed is None:
            return MatchScore(
                match_type=MatchType.DATE,
                score=0,
                weight=self.settings.date_weight,
                details={"reason": "invalid_date_format"},
            )

        # Exact match
        if entry_parsed == wikidata_parsed:
            return MatchScore(
                match_type=MatchType.DATE,
                score=self.settings.date_exact_score,
                weight=self.settings.date_weight,
                details={"matched": "exact"},
            )

        # Close match within tolerance
        diff_days = abs((entry_parsed - wikidata_parsed).days)
        if diff_days <= self.settings.date_tolerance_days:
            # Scale score based on how close
            score = int(
                self.settings.date_exact_score
                - (diff_days * 5)  # Lose 5 points per day difference
            )
            return MatchScore(
                match_type=MatchType.DATE,
                score=max(score, self.settings.date_year_only_score),
                weight=self.settings.date_weight,
                details={"matched": "close", "diff_days": diff_days},
            )

        # Year-only match
        if entry_parsed.year == wikidata_parsed.year:
            return MatchScore(
                match_type=MatchType.DATE,
                score=self.settings.date_year_only_score,
                weight=self.settings.date_weight,
                details={"matched": "year_only", "year": entry_parsed.year},
            )

        # No match
        return MatchScore(
            match_type=MatchType.DATE,
            score=0,
            weight=self.settings.date_weight,
            details={"matched": "none", "diff_years": abs(entry_parsed.year - wikidata_parsed.year)},
        )

    def _parse_date(self, value: date | str) -> date | None:
        """Parse a date value to a date object."""
        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, str):
            # Strip leading + (Wikidata format) and whitespace
            value = value.strip().lstrip("+")

            # Try common formats
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    parsed = datetime.strptime(value[:len(fmt.replace('%', ''))+value.count('-')], fmt)
                    return parsed.date()
                except ValueError:
                    continue

            # Try ISO format with just date portion
            try:
                date_part = value[:10]
                if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
                    return datetime.strptime(date_part, "%Y-%m-%d").date()
            except ValueError:
                pass

            # Try year only
            try:
                year = int(value[:4])
                if 1 <= year <= 9999:
                    return date(year, 1, 1)
            except (ValueError, IndexError):
                pass

        return None


# =============================================================================
# Score Calculator (Orchestrator)
# =============================================================================


class ScoreCalculator:
    """
    Orchestrates matching across multiple criteria and computes composite scores.
    """

    def __init__(self, settings: MatchingSettings | None = None):
        self.settings = settings or get_settings().matching
        self.name_matcher = NameMatcher(settings)
        self.date_matcher = DateMatcher(settings)

    def calculate(
        self,
        entry_data: dict[str, Any],
        wikidata_entity: dict[str, Any],
    ) -> CompositeScore:
        """
        Calculate composite match score between entry and Wikidata entity.

        Args:
            entry_data: Dict with entry fields (name, dob, properties, etc.)
            wikidata_entity: Dict with Wikidata fields (label, description, aliases, claims)

        Returns:
            CompositeScore with weighted average and individual scores
        """
        scores: list[MatchScore] = []
        matched_fields: list[str] = []

        # Name matching
        entry_name = entry_data.get("name") or entry_data.get("display_name")
        wikidata_label = wikidata_entity.get("label")
        wikidata_aliases = wikidata_entity.get("aliases")

        if entry_name and wikidata_label:
            name_score = self.name_matcher.compare(entry_name, wikidata_label, wikidata_aliases)
            scores.append(name_score)
            if name_score.score >= self.settings.name_fuzzy_threshold:
                matched_fields.append("name")

        # Date matching (if DOB available)
        entry_dob = entry_data.get("dob") or entry_data.get("date_of_birth")
        wikidata_dob = self._extract_wikidata_date(wikidata_entity, "P569")  # P569 = date of birth

        if entry_dob or wikidata_dob:
            date_score = self.date_matcher.compare(entry_dob, wikidata_dob)
            scores.append(date_score)
            if date_score.score > 0:
                matched_fields.append("dob")

        # Calculate weighted average
        if not scores:
            return CompositeScore(
                total_score=0,
                scores=scores,
                confidence="none",
                matched_fields=matched_fields,
            )

        total_weight = sum(s.weight for s in scores)
        if total_weight == 0:
            weighted_avg = 0
        else:
            weighted_avg = sum(s.score * s.weight for s in scores) / total_weight

        total_score = int(round(weighted_avg))

        # Determine confidence level
        confidence = self._determine_confidence(total_score, matched_fields)

        return CompositeScore(
            total_score=total_score,
            scores=scores,
            confidence=confidence,
            matched_fields=matched_fields,
        )

    def _determine_confidence(self, score: int, matched_fields: list[str]) -> str:
        """Determine confidence level based on score and matched fields."""
        if score >= self.settings.auto_accept_threshold:
            return "high"
        elif score >= self.settings.high_confidence_threshold:
            return "high" if len(matched_fields) >= 2 else "medium"
        elif score >= self.settings.low_confidence_threshold:
            return "medium"
        else:
            return "low"

    def _extract_wikidata_date(
        self, entity: dict[str, Any], property_id: str
    ) -> str | None:
        """Extract a date from Wikidata claims."""
        claims = entity.get("claims", {})
        prop_claims = claims.get(property_id, [])

        if not prop_claims:
            return None

        # Get first claim's value
        try:
            mainsnak = prop_claims[0].get("mainsnak", {})
            datavalue = mainsnak.get("datavalue", {})
            value = datavalue.get("value", {})

            if isinstance(value, dict):
                return value.get("time")
            return None
        except (IndexError, KeyError, TypeError):
            return None


# =============================================================================
# Factory Functions
# =============================================================================


def get_score_calculator() -> ScoreCalculator:
    """Factory function for ScoreCalculator."""
    return ScoreCalculator()


def get_name_matcher() -> NameMatcher:
    """Factory function for NameMatcher."""
    return NameMatcher()


def get_date_matcher() -> DateMatcher:
    """Factory function for DateMatcher."""
    return DateMatcher()
