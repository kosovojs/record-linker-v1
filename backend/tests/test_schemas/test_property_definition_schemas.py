"""Tests for PropertyDefinition request/response schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.enums import PropertyDataType
from app.schemas.property_definition import (
    PropertyDefinitionBase,
    PropertyDefinitionCreate,
    PropertyDefinitionRead,
    PropertyDefinitionUpdate,
)


class TestPropertyDefinitionBase:
    """Tests for PropertyDefinitionBase schema."""

    def test_valid_property_definition_base(self):
        """Test creating valid PropertyDefinitionBase."""
        prop = PropertyDefinitionBase(
            name="date_of_birth",
            display_name="Date of Birth",
        )
        assert prop.name == "date_of_birth"
        assert prop.data_type_hint == PropertyDataType.TEXT

    def test_name_pattern_validation(self):
        """Test name must be lowercase with underscores."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyDefinitionBase(
                name="Invalid-Name",  # Hyphens not allowed
                display_name="Test",
            )
        assert "name" in str(exc_info.value)

    def test_valid_name_patterns(self):
        """Test various valid name patterns."""
        valid_names = ["name", "date_of_birth", "full_name", "id123"]
        for name in valid_names:
            prop = PropertyDefinitionBase(name=name, display_name="Test")
            assert prop.name == name

    def test_default_values(self):
        """Test default values are set correctly."""
        prop = PropertyDefinitionBase(name="test", display_name="Test")
        assert prop.is_multivalued is False
        assert prop.is_searchable is True
        assert prop.is_display_field is False
        assert prop.display_order == 0


class TestPropertyDefinitionCreate:
    """Tests for PropertyDefinitionCreate schema."""

    def test_valid_create_with_wikidata(self):
        """Test creating with Wikidata property."""
        prop = PropertyDefinitionCreate(
            name="date_of_birth",
            display_name="Date of Birth",
            data_type_hint=PropertyDataType.DATE,
            wikidata_property="P569",
        )
        assert prop.wikidata_property == "P569"
        assert prop.data_type_hint == PropertyDataType.DATE

    def test_invalid_wikidata_property_pattern(self):
        """Test that invalid Wikidata property format is rejected."""
        with pytest.raises(ValidationError):
            PropertyDefinitionCreate(
                name="test",
                display_name="Test",
                wikidata_property="Q123",  # Should be P prefix
            )


class TestPropertyDefinitionUpdate:
    """Tests for PropertyDefinitionUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid."""
        update = PropertyDefinitionUpdate()
        assert update.name is None

    def test_partial_update(self):
        """Test partial update."""
        update = PropertyDefinitionUpdate(
            display_name="New Label",
            is_searchable=False,
        )
        assert update.display_name == "New Label"
        assert update.is_searchable is False


class TestPropertyDefinitionRead:
    """Tests for PropertyDefinitionRead schema."""

    def test_valid_property_definition_read(self):
        """Test creating PropertyDefinitionRead."""
        now = datetime.utcnow()
        prop = PropertyDefinitionRead(
            uuid=uuid4(),
            name="country",
            display_name="Country",
            description="Country of nationality",
            data_type_hint="text",
            is_multivalued=True,
            is_searchable=True,
            is_display_field=False,
            display_order=5,
            wikidata_property="P27",
            validation_regex=None,
            created_at=now,
            updated_at=now,
        )
        assert prop.name == "country"
        assert prop.wikidata_property == "P27"
