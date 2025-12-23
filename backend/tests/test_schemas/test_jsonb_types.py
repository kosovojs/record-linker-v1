"""Tests for JSONB typed schemas."""

import pytest

from app.schemas.jsonb_types import (
    CandidateExtraData,
    CandidateMatchedProperties,
    CandidateScoreBreakdown,
    DatasetEntryExtraData,
    DatasetExtraData,
    MatchingWeights,
    ProjectConfig,
    PropertyMatch,
    SearchStrategy,
    TaskExtraData,
    UserSettings,
)


class TestUserSettings:
    """Test UserSettings schema."""

    def test_default_values(self):
        """Test defaults are set correctly."""
        settings = UserSettings()
        assert settings.notifications.email_on_task_complete is True
        assert settings.ui.theme == "system"
        assert settings.ui.items_per_page == 20
        assert settings.feature_flags == {}

    def test_custom_values(self):
        """Test custom values can be set."""
        settings = UserSettings(
            ui={"theme": "dark", "language": "lv"},
            feature_flags={"beta_feature": True},
        )
        assert settings.ui.theme == "dark"
        assert settings.ui.language == "lv"
        assert settings.feature_flags["beta_feature"] is True

    def test_serialization(self):
        """Test model can be serialized to dict for DB storage."""
        settings = UserSettings()
        data = settings.model_dump()
        assert isinstance(data, dict)
        assert "notifications" in data
        assert "ui" in data


class TestProjectConfig:
    """Test ProjectConfig schema."""

    def test_default_values(self):
        """Test defaults are set correctly."""
        config = ProjectConfig()
        assert config.auto_accept_threshold is None
        assert config.max_candidates_per_task == 20
        assert config.parallel_workers == 4
        assert config.schema_version == 1

    def test_matching_weights(self):
        """Test matching weights defaults."""
        config = ProjectConfig()
        assert config.matching_weights.name_similarity == 0.4
        assert config.matching_weights.date_of_birth == 0.3

    def test_search_strategies(self):
        """Test search strategies can be configured."""
        config = ProjectConfig(
            search_strategies=[
                SearchStrategy(strategy_type="wikidata_search", max_results=5),
                SearchStrategy(strategy_type="sparql_query", enabled=False),
            ]
        )
        assert len(config.search_strategies) == 2
        assert config.search_strategies[0].strategy_type == "wikidata_search"
        assert config.search_strategies[1].enabled is False

    def test_threshold_validation(self):
        """Test threshold values are validated."""
        # Valid thresholds
        config = ProjectConfig(
            auto_accept_threshold=90,
            auto_reject_threshold=30,
        )
        assert config.auto_accept_threshold == 90

        # Invalid threshold should raise
        with pytest.raises(ValueError):
            ProjectConfig(auto_accept_threshold=150)  # > 100


class TestCandidateScoring:
    """Test candidate scoring schemas."""

    def test_property_match(self):
        """Test PropertyMatch schema."""
        match = PropertyMatch(
            property_id="P569",
            source_value="1990-05-15",
            wikidata_value="1990-05-15",
            match_score=100,
            match_type="exact",
        )
        assert match.match_score == 100
        assert match.match_type == "exact"

    def test_score_breakdown(self):
        """Test CandidateScoreBreakdown schema."""
        breakdown = CandidateScoreBreakdown(
            property_scores={"P569": 100, "P27": 80},
            weights_applied={"P569": 0.3, "P27": 0.2},
            raw_score=88.5,
            normalized_score=89,
        )
        assert breakdown.property_scores["P569"] == 100
        assert breakdown.normalized_score == 89

    def test_matched_properties(self):
        """Test CandidateMatchedProperties schema."""
        matched = CandidateMatchedProperties(
            properties=[
                PropertyMatch(property_id="P569", match_score=100, match_type="exact"),
                PropertyMatch(property_id="P27", match_score=75, match_type="fuzzy"),
            ],
            exact_matches=1,
            fuzzy_matches=1,
        )
        assert len(matched.properties) == 2
        assert matched.exact_matches == 1


class TestDatasetExtraData:
    """Test DatasetExtraData schema."""

    def test_default_values(self):
        """Test defaults are set correctly."""
        extra = DatasetExtraData()
        assert extra.schema_version == 1
        assert extra.field_mappings == {}

    def test_field_mappings(self):
        """Test field mappings can be set."""
        extra = DatasetExtraData(
            field_mappings={
                "player_name": "full_name",
                "dob": "date_of_birth",
            }
        )
        assert extra.field_mappings["dob"] == "date_of_birth"


class TestTaskExtraData:
    """Test TaskExtraData schema."""

    def test_default_values(self):
        """Test defaults are set correctly."""
        extra = TaskExtraData()
        assert extra.retry_count == 0
        assert extra.tags == []

    def test_processing_info(self):
        """Test processing info can be set."""
        extra = TaskExtraData(
            processing={"search_queries_used": ["John Smith hockey"], "processing_time_seconds": 1.5}
        )
        assert extra.processing.search_queries_used[0] == "John Smith hockey"
        assert extra.processing.processing_time_seconds == 1.5
