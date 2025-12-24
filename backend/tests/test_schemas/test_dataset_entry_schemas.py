"""Tests for DatasetEntry request/response schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.dataset_entry import (
    DatasetEntryBase,
    DatasetEntryCreate,
    DatasetEntryRead,
    DatasetEntryUpdate,
)
from app.schemas.jsonb_types import DatasetEntryExtraData


class TestDatasetEntryBase:
    """Tests for DatasetEntryBase schema."""

    def test_valid_dataset_entry_base(self):
        """Test creating valid DatasetEntryBase."""
        entry = DatasetEntryBase(
            external_id="player-12345",
        )
        assert entry.external_id == "player-12345"
        assert entry.external_url is None
        assert entry.display_name is None

    def test_empty_external_id_rejected(self):
        """Test that empty external_id is rejected."""
        with pytest.raises(ValidationError):
            DatasetEntryBase(external_id="")


class TestDatasetEntryCreate:
    """Tests for DatasetEntryCreate schema."""

    def test_valid_create_minimal(self):
        """Test creating with minimal fields."""
        entry = DatasetEntryCreate(
            external_id="12345",
            dataset_uuid=uuid4(),
        )
        assert entry.raw_data is None
        assert entry.extra_data is None

    def test_valid_create_full(self):
        """Test creating with all fields."""
        entry = DatasetEntryCreate(
            external_id="actor-789",
            dataset_uuid=uuid4(),
            external_url="https://imdb.com/name/nm0000001",
            display_name="Tom Hanks",
            raw_data={"name": "Tom Hanks", "imdb_id": "nm0000001"},
            extra_data=DatasetEntryExtraData(),
        )
        assert entry.display_name == "Tom Hanks"
        assert entry.raw_data["imdb_id"] == "nm0000001"


class TestDatasetEntryUpdate:
    """Tests for DatasetEntryUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid."""
        update = DatasetEntryUpdate()
        assert update.external_id is None

    def test_partial_update(self):
        """Test partial update."""
        update = DatasetEntryUpdate(
            display_name="Updated Name",
        )
        assert update.display_name == "Updated Name"


class TestDatasetEntryRead:
    """Tests for DatasetEntryRead schema."""

    def test_valid_dataset_entry_read(self):
        """Test creating DatasetEntryRead."""
        now = datetime.utcnow()
        entry = DatasetEntryRead(
            uuid=uuid4(),
            dataset_uuid=uuid4(),
            external_id="12345",
            external_url="https://example.com/12345",
            display_name="Test Entry",
            raw_data={"key": "value"},
            extra_data={},
            created_at=now,
            updated_at=now,
        )
        assert entry.external_id == "12345"
        assert entry.raw_data["key"] == "value"
