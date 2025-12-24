"""Tests for DatasetEntryProperty request/response schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.dataset_entry_property import (
    DatasetEntryPropertyBase,
    DatasetEntryPropertyCreate,
    DatasetEntryPropertyRead,
    DatasetEntryPropertyUpdate,
)
from app.schemas.enums import PropertyValueSource


class TestDatasetEntryPropertyBase:
    """Tests for DatasetEntryPropertyBase schema."""

    def test_valid_base(self):
        """Test creating valid DatasetEntryPropertyBase."""
        prop = DatasetEntryPropertyBase(value="John Doe")
        assert prop.value == "John Doe"
        assert prop.source == PropertyValueSource.IMPORT
        assert prop.ordinal == 0

    def test_empty_value_rejected(self):
        """Test that empty value is rejected."""
        with pytest.raises(ValidationError):
            DatasetEntryPropertyBase(value="")

    def test_confidence_range(self):
        """Test confidence must be 0-100."""
        # Valid range
        prop = DatasetEntryPropertyBase(value="test", confidence=75)
        assert prop.confidence == 75

        # Out of range
        with pytest.raises(ValidationError):
            DatasetEntryPropertyBase(value="test", confidence=150)

        with pytest.raises(ValidationError):
            DatasetEntryPropertyBase(value="test", confidence=-1)


class TestDatasetEntryPropertyCreate:
    """Tests for DatasetEntryPropertyCreate schema."""

    def test_valid_create(self):
        """Test creating with required UUIDs."""
        prop = DatasetEntryPropertyCreate(
            value="1990-05-15",
            dataset_entry_uuid=uuid4(),
            property_uuid=uuid4(),
            source=PropertyValueSource.IMPORT,
        )
        assert prop.value == "1990-05-15"


class TestDatasetEntryPropertyUpdate:
    """Tests for DatasetEntryPropertyUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid."""
        update = DatasetEntryPropertyUpdate()
        assert update.value is None

    def test_partial_update(self):
        """Test partial update."""
        update = DatasetEntryPropertyUpdate(
            value="Updated Value",
            confidence=95,
        )
        assert update.value == "Updated Value"
        assert update.confidence == 95


class TestDatasetEntryPropertyRead:
    """Tests for DatasetEntryPropertyRead schema."""

    def test_valid_read(self):
        """Test creating DatasetEntryPropertyRead."""
        now = datetime.utcnow()
        prop = DatasetEntryPropertyRead(
            uuid=uuid4(),
            dataset_entry_uuid=uuid4(),
            property_uuid=uuid4(),
            value="Test Value",
            value_normalized="test value",
            confidence=80,
            source="import",
            ordinal=0,
            created_at=now,
            updated_at=now,
        )
        assert prop.value == "Test Value"
        assert prop.confidence == 80
