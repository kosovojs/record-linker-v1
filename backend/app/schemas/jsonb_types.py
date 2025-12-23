"""
Typed Pydantic models for JSONB columns.

These models define the expected structure of JSONB fields in our models.
Using typed schemas instead of raw dicts prevents data structure drift
and makes the codebase more maintainable.

Usage in service layer:
    # Validate config before saving
    config = ProjectConfig(**raw_config_dict)
    project.config = config.model_dump()

    # Parse config from DB
    config = ProjectConfig.model_validate(project.config)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# User Settings
# =============================================================================


class NotificationPreferences(BaseModel):
    """User notification preferences."""

    email_on_task_complete: bool = True
    email_on_project_complete: bool = True
    email_digest_frequency: str = "daily"  # never, daily, weekly


class UIPreferences(BaseModel):
    """User interface preferences."""

    theme: str = "system"  # light, dark, system
    language: str = "en"
    items_per_page: int = 20
    show_score_breakdown: bool = True
    auto_expand_candidates: bool = False


class UserSettings(BaseModel):
    """
    Structure for users.settings JSONB column.

    Contains user preferences that don't warrant separate DB columns.
    """

    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)
    ui: UIPreferences = Field(default_factory=UIPreferences)

    # Feature flags - can enable experimental features per user
    feature_flags: dict[str, bool] = Field(default_factory=dict)

    # Arbitrary key-value for extensibility (keep this minimal)
    custom: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Dataset Extra Data
# =============================================================================

class DatasetSourceInfo(BaseModel):
    """Information about the data source."""

    api_version: str | None = None
    scraper_version: str | None = None
    license: str | None = None
    contact_email: str | None = None
    documentation_url: str | None = None


class DatasetExtraData(BaseModel):
    """
    Structure for datasets.extra_data JSONB column.

    Contains source-specific metadata that varies per dataset.
    """

    source_info: DatasetSourceInfo = Field(default_factory=DatasetSourceInfo)

    # Schema versioning - helps with migrations
    schema_version: int = 1

    # Import statistics
    last_import_count: int | None = None
    last_import_duration_seconds: float | None = None

    # Field mappings from source to our properties
    # e.g., {"player_name": "full_name", "dob": "date_of_birth"}
    field_mappings: dict[str, str] = Field(default_factory=dict)

    # Notes about this dataset
    notes: str | None = None


# =============================================================================
# DatasetEntry Extra Data
# =============================================================================

class DatasetEntryExtraData(BaseModel):
    """
    Structure for dataset_entries.extra_data JSONB column.

    Contains import-specific metadata for individual entries.
    """

    # Import tracking
    imported_at: datetime | None = None
    import_batch_id: str | None = None

    # Source-specific IDs that don't fit in external_id
    alternate_ids: dict[str, str] = Field(default_factory=dict)

    # Quality flags
    has_warnings: bool = False
    warnings: list[str] = Field(default_factory=list)

    # Schema version
    schema_version: int = 1


# =============================================================================
# Project Config
# =============================================================================

class MatchingWeights(BaseModel):
    """Weights for different properties in matching score calculation."""

    name_similarity: float = 0.4
    date_of_birth: float = 0.3
    nationality: float = 0.15
    other_properties: float = 0.15


class SearchStrategy(BaseModel):
    """Configuration for a search strategy."""

    strategy_type: str  # wikidata_search, sparql_query, wbgetentities
    enabled: bool = True
    max_results: int = 10
    min_score_threshold: int = 50


class ProjectConfig(BaseModel):
    """
    Structure for projects.config JSONB column.

    Contains matching parameters and search configuration.
    """

    # Auto-accept candidates above this score (0-100, None = never auto-accept)
    auto_accept_threshold: int | None = Field(default=None, ge=0, le=100)

    # Auto-reject candidates below this score
    auto_reject_threshold: int | None = Field(default=None, ge=0, le=100)

    # Property weights for scoring
    matching_weights: MatchingWeights = Field(default_factory=MatchingWeights)

    # Which search strategies to use
    search_strategies: list[SearchStrategy] = Field(default_factory=list)

    # Wikidata entity types to search for (P31 values)
    # e.g., ["Q5"] for humans, ["Q476028"] for association football players
    target_entity_types: list[str] = Field(default_factory=list)

    # Properties to compare during matching
    properties_to_match: list[str] = Field(
        default_factory=lambda: ["P569", "P570", "P27", "P106"]  # DOB, DOD, nationality, occupation
    )

    # Processing options
    max_candidates_per_task: int = Field(default=20, ge=1, le=100)
    parallel_workers: int = Field(default=4, ge=1, le=20)

    # Schema version
    schema_version: int = 1


# =============================================================================
# Task Extra Data
# =============================================================================

class TaskProcessingInfo(BaseModel):
    """Information about task processing."""

    search_queries_used: list[str] = Field(default_factory=list)
    strategies_executed: list[str] = Field(default_factory=list)
    processing_time_seconds: float | None = None
    worker_id: str | None = None


class TaskExtraData(BaseModel):
    """
    Structure for tasks.extra_data JSONB column.

    Contains processing metadata and debugging info.
    """

    processing: TaskProcessingInfo = Field(default_factory=TaskProcessingInfo)

    # Retry tracking
    retry_count: int = 0
    last_error: str | None = None

    # Manual review notes from reviewer
    review_notes: str | None = None

    # Tags for filtering
    tags: list[str] = Field(default_factory=list)

    # Schema version
    schema_version: int = 1


# =============================================================================
# MatchCandidate Extra Data & Score Breakdown
# =============================================================================

class PropertyMatch(BaseModel):
    """Details of how a single property matched."""

    property_id: str  # Wikidata property ID like P569
    source_value: str | None = None  # Value from dataset entry
    wikidata_value: str | None = None  # Value from Wikidata
    match_score: int = Field(ge=0, le=100)  # How well they matched
    match_type: str = "exact"  # exact, fuzzy, partial, none


class CandidateScoreBreakdown(BaseModel):
    """
    Structure for match_candidates.score_breakdown JSONB column.

    Shows how the overall score was calculated.
    """

    # Individual property scores
    property_scores: dict[str, int] = Field(default_factory=dict)

    # Weights used
    weights_applied: dict[str, float] = Field(default_factory=dict)

    # Bonus/penalty adjustments
    adjustments: list[dict[str, Any]] = Field(default_factory=list)

    # Final calculation
    raw_score: float = 0.0
    normalized_score: int = 0  # The 0-100 integer score


class CandidateMatchedProperties(BaseModel):
    """
    Structure for match_candidates.matched_properties JSONB column.

    Detailed comparison of each property.
    """

    properties: list[PropertyMatch] = Field(default_factory=list)

    # Summary counts
    exact_matches: int = 0
    fuzzy_matches: int = 0
    mismatches: int = 0
    missing_in_source: int = 0
    missing_in_wikidata: int = 0


class CandidateExtraData(BaseModel):
    """
    Structure for match_candidates.extra_data JSONB column.

    Contains source-specific and debugging information.
    """

    # How candidate was found
    search_query: str | None = None
    search_rank: int | None = None  # Position in search results

    # Wikidata item info (cached for display, not authoritative)
    wikidata_label: str | None = None
    wikidata_description: str | None = None

    # Import info (for file-imported candidates)
    import_batch_id: str | None = None
    import_row_number: int | None = None

    # AI suggestion info
    ai_model: str | None = None
    ai_confidence: float | None = None

    # Schema version
    schema_version: int = 1


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # User
    "UserSettings",
    "NotificationPreferences",
    "UIPreferences",
    # Dataset
    "DatasetExtraData",
    "DatasetSourceInfo",
    # DatasetEntry
    "DatasetEntryExtraData",
    # Project
    "ProjectConfig",
    "MatchingWeights",
    "SearchStrategy",
    # Task
    "TaskExtraData",
    "TaskProcessingInfo",
    # MatchCandidate
    "CandidateScoreBreakdown",
    "CandidateMatchedProperties",
    "CandidateExtraData",
    "PropertyMatch",
]
