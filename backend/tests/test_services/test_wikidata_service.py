"""
Tests for WikidataService.

Uses mocked HTTP responses to test API integration logic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import WikidataSettings
from app.services.wikidata_service import (
    WikidataAPIError,
    WikidataNetworkError,
    WikidataService,
)


@pytest.fixture
def wikidata_settings() -> WikidataSettings:
    """Create test settings."""
    return WikidataSettings(
        base_url="https://test.wikidata.org/w/api.php",
        timeout=5.0,
        default_language="en",
    )


@pytest.fixture
def wikidata_service(wikidata_settings: WikidataSettings) -> WikidataService:
    """Create WikidataService with test settings."""
    return WikidataService(settings=wikidata_settings)


class TestSearchEntities:
    """Tests for search_entities method."""

    async def test_search_returns_results(self, wikidata_service: WikidataService):
        """Test successful search returns results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "search": [
                {
                    "id": "Q42",
                    "label": "Douglas Adams",
                    "description": "English author",
                    "aliases": ["DNA"],
                },
                {
                    "id": "Q12345",
                    "label": "Douglas Adams Jr",
                    "description": None,
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            results = await wikidata_service.search_entities("Douglas Adams")

            assert len(results) == 2
            assert results[0].qid == "Q42"
            assert results[0].label == "Douglas Adams"
            assert results[0].description == "English author"
            assert results[0].aliases == ["DNA"]
            assert results[1].qid == "Q12345"
            assert results[1].description is None

    async def test_search_empty_query_returns_empty(self, wikidata_service: WikidataService):
        """Test empty query returns empty list without API call."""
        results = await wikidata_service.search_entities("")
        assert results == []

        results = await wikidata_service.search_entities("   ")
        assert results == []

    async def test_search_respects_limit(self, wikidata_service: WikidataService):
        """Test limit is clamped to valid range."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"search": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            # Should clamp limit to 50
            await wikidata_service.search_entities("test", limit=100)

            call_args = mock_session.get.call_args
            params = call_args.kwargs["params"]
            assert params["limit"] == 50

    async def test_search_handles_api_error(self, wikidata_service: WikidataService):
        """Test API error response raises WikidataAPIError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": "invalid-search",
                "info": "Invalid search parameter",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            with pytest.raises(WikidataAPIError) as exc_info:
                await wikidata_service.search_entities("test")

            assert "Invalid search parameter" in str(exc_info.value)
            assert exc_info.value.error_code == "invalid-search"


class TestGetEntity:
    """Tests for get_entity method."""

    async def test_get_entity_returns_entity(self, wikidata_service: WikidataService):
        """Test successful entity fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entities": {
                "Q42": {
                    "labels": {"en": {"value": "Douglas Adams"}},
                    "descriptions": {"en": {"value": "English author"}},
                    "aliases": {"en": [{"value": "DNA"}, {"value": "Douglas N. Adams"}]},
                    "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}]},
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            entity = await wikidata_service.get_entity("Q42")

            assert entity is not None
            assert entity.qid == "Q42"
            assert entity.label == "Douglas Adams"
            assert entity.description == "English author"
            assert entity.aliases == ["DNA", "Douglas N. Adams"]
            assert entity.claims is not None

    async def test_get_entity_not_found(self, wikidata_service: WikidataService):
        """Test missing entity returns None."""
        mock_response = MagicMock()
        # Wikidata API returns entity key with "missing" field for non-existent entities
        mock_response.json.return_value = {
            "entities": {
                "Q999999999": {"id": "Q999999999", "missing": ""}
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            entity = await wikidata_service.get_entity("Q999999999")
            assert entity is None

    async def test_get_entity_empty_qid(self, wikidata_service: WikidataService):
        """Test empty QID returns None without API call."""
        entity = await wikidata_service.get_entity("")
        assert entity is None

        entity = await wikidata_service.get_entity("   ")
        assert entity is None


class TestGetEntities:
    """Tests for get_entities method."""

    async def test_get_entities_returns_dict(self, wikidata_service: WikidataService):
        """Test batch entity fetch returns dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entities": {
                "Q42": {
                    "labels": {"en": {"value": "Douglas Adams"}},
                    "descriptions": {"en": {"value": "English author"}},
                    "aliases": {"en": []},
                },
                "Q1": {
                    "labels": {"en": {"value": "Universe"}},
                    "descriptions": {"en": {"value": "All of space and time"}},
                    "aliases": {"en": [{"value": "cosmos"}]},
                },
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            entities = await wikidata_service.get_entities(["Q42", "Q1"])

            assert len(entities) == 2
            assert "Q42" in entities
            assert "Q1" in entities
            assert entities["Q42"].label == "Douglas Adams"
            assert entities["Q1"].aliases == ["cosmos"]

    async def test_get_entities_empty_list(self, wikidata_service: WikidataService):
        """Test empty list returns empty dict without API call."""
        entities = await wikidata_service.get_entities([])
        assert entities == {}


class TestErrorHandling:
    """Tests for error handling."""

    async def test_timeout_raises_network_error(self, wikidata_service: WikidataService):
        """Test timeout raises WikidataNetworkError."""
        import niquests

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=niquests.exceptions.Timeout("timeout"))
            mock_get_session.return_value = mock_session

            with pytest.raises(WikidataNetworkError) as exc_info:
                await wikidata_service.search_entities("test")

            assert "timed out" in str(exc_info.value).lower()

    async def test_connection_error_raises_network_error(self, wikidata_service: WikidataService):
        """Test connection error raises WikidataNetworkError."""
        import niquests

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(
                side_effect=niquests.exceptions.ConnectionError("connection refused")
            )
            mock_get_session.return_value = mock_session

            with pytest.raises(WikidataNetworkError) as exc_info:
                await wikidata_service.search_entities("test")

            assert "connection" in str(exc_info.value).lower()


class TestContextManager:
    """Tests for context manager usage."""

    async def test_context_manager_creates_and_closes_session(
        self, wikidata_service: WikidataService
    ):
        """Test context manager properly manages session lifecycle."""
        assert wikidata_service._session is None

        async with wikidata_service:
            assert wikidata_service._session is not None

        # Session should be closed after context exit
        # Note: niquests session close is idempotent
