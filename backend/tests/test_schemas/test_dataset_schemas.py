"""Tests for Dataset request/response schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.dataset import DatasetBase, DatasetCreate, DatasetRead, DatasetUpdate
from app.schemas.enums import DatasetSourceType
from app.schemas.jsonb_types import DatasetExtraData


class TestDatasetBase:
    """Tests for DatasetBase schema."""

    def test_valid_dataset_base(self):
        """Test creating valid DatasetBase."""
        dataset = DatasetBase(
            name="EliteProspects Players",
            slug="eliteprospects-players",
            entity_type="person",
        )
        assert dataset.name == "EliteProspects Players"
        assert dataset.slug == "eliteprospects-players"
        assert dataset.source_type == DatasetSourceType.WEB_SCRAPE

    def test_slug_pattern_validation(self):
        """Test slug must be lowercase with hyphens."""
        with pytest.raises(ValidationError) as exc_info:
            DatasetBase(
                name="Test",
                slug="Invalid_Slug",  # Underscores not allowed
                entity_type="person",
            )
        assert "slug" in str(exc_info.value)

    def test_valid_slug_patterns(self):
        """Test various valid slug patterns."""
        valid_slugs = ["test", "test-data", "my-dataset-v2", "a1b2c3"]
        for slug in valid_slugs:
            dataset = DatasetBase(name="Test", slug=slug, entity_type="person")
            assert dataset.slug == slug

    def test_empty_name_rejected(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError):
            DatasetBase(name="", slug="test", entity_type="person")


class TestDatasetCreate:
    """Tests for DatasetCreate schema."""

    def test_valid_dataset_create_minimal(self):
        """Test creating dataset with minimal fields."""
        dataset = DatasetCreate(
            name="Test Dataset",
            slug="test-dataset",
            entity_type="organization",
        )
        assert dataset.extra_data is None
        assert dataset.source_type == DatasetSourceType.WEB_SCRAPE

    def test_valid_dataset_create_full(self):
        """Test creating dataset with all fields."""
        extra_data = DatasetExtraData()
        dataset = DatasetCreate(
            name="IMDB Actors",
            slug="imdb-actors",
            description="Actor profiles from IMDB",
            source_url="https://imdb.com",
            source_type=DatasetSourceType.API,
            entity_type="person",
            extra_data=extra_data,
        )
        assert dataset.source_type == DatasetSourceType.API
        assert dataset.source_url == "https://imdb.com"


class TestDatasetUpdate:
    """Tests for DatasetUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid."""
        update = DatasetUpdate()
        assert update.name is None
        assert update.slug is None

    def test_partial_update(self):
        """Test partial update."""
        update = DatasetUpdate(
            name="Updated Name",
            source_type=DatasetSourceType.FILE_IMPORT,
        )
        assert update.name == "Updated Name"
        assert update.source_type == DatasetSourceType.FILE_IMPORT
        assert update.slug is None


class TestDatasetRead:
    """Tests for DatasetRead schema."""

    def test_valid_dataset_read(self):
        """Test creating DatasetRead."""
        now = datetime.utcnow()
        dataset = DatasetRead(
            uuid=uuid4(),
            name="Test Dataset",
            slug="test-dataset",
            description=None,
            source_url=None,
            source_type=DatasetSourceType.WEB_SCRAPE,
            entity_type="person",
            entry_count=1000,
            last_synced_at=now,
            extra_data={},
            created_at=now,
            updated_at=now,
        )
        assert dataset.entry_count == 1000
        assert dataset.source_type == DatasetSourceType.WEB_SCRAPE
