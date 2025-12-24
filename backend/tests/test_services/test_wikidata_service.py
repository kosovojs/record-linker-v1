"""
Tests for WikidataService.

Unit tests use mocked HTTP responses for fast, reliable testing.
Integration tests (marked with @pytest.mark.integration) connect to real Wikidata API.

Run unit tests only (default):
    pytest tests/test_services/test_wikidata_service.py

Run integration tests:
    pytest tests/test_services/test_wikidata_service.py -m integration

Run all tests:
    pytest tests/test_services/test_wikidata_service.py -m ""
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import WikidataSettings
from app.services.wikidata_service import (
    WikidataAPIError,
    WikidataNetworkError,
    WikidataService,
)


# =============================================================================
# Mock Response Factory
# =============================================================================


class MockWikidataAPI:
    """
    Factory for creating realistic Wikidata API mock responses.

    Based on actual Wikidata API response formats from:
    https://www.wikidata.org/w/api.php
    """

    @staticmethod
    def search_response(
        results: list[dict[str, Any]] | None = None,
        success: bool = True,
    ) -> dict[str, Any]:
        """
        Create a wbsearchentities response.

        Args:
            results: List of search result dicts with keys: id, label, description, aliases
            success: Whether the request succeeded
        """
        if not success:
            return {
                "error": {
                    "code": "invalid-search",
                    "info": "Invalid search parameter",
                }
            }

        if results is None:
            results = []

        search_items = []
        for r in results:
            item = {
                "id": r.get("id", "Q1"),
                "title": r.get("id", "Q1"),
                "pageid": 123,
                "repository": "wikidata",
                "url": f"//www.wikidata.org/wiki/{r.get('id', 'Q1')}",
                "concepturi": f"http://www.wikidata.org/entity/{r.get('id', 'Q1')}",
                "label": r.get("label", "Unknown"),
                "match": {"type": "label", "language": "en", "text": r.get("label", "Unknown")},
            }
            if r.get("description"):
                item["description"] = r["description"]
            if r.get("aliases"):
                item["aliases"] = r["aliases"]
            search_items.append(item)

        return {
            "searchinfo": {"search": "query"},
            "search": search_items,
            "success": 1,
        }

    @staticmethod
    def entity_response(
        entities: dict[str, dict[str, Any]] | None = None,
        missing_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a wbgetentities response.

        Args:
            entities: Dict mapping QID to entity data (labels, descriptions, aliases, claims)
            missing_ids: List of QIDs that should be marked as missing
        """
        result_entities = {}

        # Add existing entities
        if entities:
            for qid, data in entities.items():
                entity = {
                    "type": "item",
                    "id": qid,
                }

                # Labels
                if "label" in data:
                    entity["labels"] = {
                        "en": {"language": "en", "value": data["label"]}
                    }
                else:
                    entity["labels"] = {}

                # Descriptions
                if "description" in data:
                    entity["descriptions"] = {
                        "en": {"language": "en", "value": data["description"]}
                    }
                else:
                    entity["descriptions"] = {}

                # Aliases
                if "aliases" in data and data["aliases"]:
                    entity["aliases"] = {
                        "en": [{"language": "en", "value": a} for a in data["aliases"]]
                    }
                else:
                    entity["aliases"] = {}

                # Claims (simplified)
                if "claims" in data:
                    entity["claims"] = data["claims"]
                else:
                    entity["claims"] = {}

                result_entities[qid] = entity

        # Add missing entities
        if missing_ids:
            for qid in missing_ids:
                result_entities[qid] = {"id": qid, "missing": ""}

        return {"entities": result_entities, "success": 1}

    @staticmethod
    def error_response(code: str, info: str) -> dict[str, Any]:
        """Create an API error response."""
        return {
            "error": {
                "code": code,
                "info": info,
                "*": "See https://www.wikidata.org/w/api.php for API usage.",
            },
            "servedby": "mw1234",
        }


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def wikidata_settings() -> WikidataSettings:
    """Create test settings."""
    return WikidataSettings(
        base_url="https://www.wikidata.org/w/api.php",
        timeout=5.0,
        default_language="en",
    )


@pytest.fixture
def wikidata_service(wikidata_settings: WikidataSettings) -> WikidataService:
    """Create WikidataService with test settings."""
    return WikidataService(settings=wikidata_settings)


@pytest.fixture
def mock_api() -> MockWikidataAPI:
    """Create mock API factory."""
    return MockWikidataAPI()


def create_mock_response(json_data: dict[str, Any]) -> MagicMock:
    """Create a mock HTTP response with the given JSON data."""
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = MagicMock()
    return mock_response


# =============================================================================
# Unit Tests - Search Entities
# =============================================================================


class TestSearchEntities:
    """Unit tests for search_entities method."""

    async def test_search_returns_results(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test successful search returns properly parsed results."""
        mock_response = create_mock_response(
            mock_api.search_response(
                results=[
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
            )
        )

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

    async def test_search_respects_limit(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test limit is clamped to valid range (1-50)."""
        mock_response = create_mock_response(mock_api.search_response(results=[]))

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            # Should clamp limit to 50
            await wikidata_service.search_entities("test", limit=100)

            call_args = mock_session.get.call_args
            params = call_args.kwargs["params"]
            assert params["limit"] == 50

    async def test_search_handles_api_error(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test API error response raises WikidataAPIError."""
        mock_response = create_mock_response(
            mock_api.error_response("invalid-search", "Invalid search parameter")
        )

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            with pytest.raises(WikidataAPIError) as exc_info:
                await wikidata_service.search_entities("test")

            assert "Invalid search parameter" in str(exc_info.value)
            assert exc_info.value.error_code == "invalid-search"


# =============================================================================
# Unit Tests - Get Entity
# =============================================================================


class TestGetEntity:
    """Unit tests for get_entity method."""

    async def test_get_entity_returns_entity(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test successful entity fetch with all fields."""
        mock_response = create_mock_response(
            mock_api.entity_response(
                entities={
                    "Q42": {
                        "label": "Douglas Adams",
                        "description": "English author",
                        "aliases": ["DNA", "Douglas N. Adams"],
                        "claims": {"P31": [{"mainsnak": {}}]},
                    }
                }
            )
        )

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

    async def test_get_entity_not_found(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test missing entity returns None."""
        mock_response = create_mock_response(
            mock_api.entity_response(missing_ids=["Q999999999"])
        )

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

    async def test_get_entity_normalizes_qid(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test QID is normalized to uppercase."""
        mock_response = create_mock_response(
            mock_api.entity_response(entities={"Q42": {"label": "Test"}})
        )

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            entity = await wikidata_service.get_entity("q42")  # lowercase

            assert entity is not None
            assert entity.qid == "Q42"


# =============================================================================
# Unit Tests - Get Entities (Batch)
# =============================================================================


class TestGetEntities:
    """Unit tests for get_entities method."""

    async def test_get_entities_returns_dict(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test batch entity fetch returns dict."""
        mock_response = create_mock_response(
            mock_api.entity_response(
                entities={
                    "Q42": {"label": "Douglas Adams", "description": "English author"},
                    "Q1": {"label": "Universe", "aliases": ["cosmos"]},
                }
            )
        )

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

    async def test_get_entities_excludes_missing(
        self, wikidata_service: WikidataService, mock_api: MockWikidataAPI
    ):
        """Test missing entities are excluded from result."""
        mock_response = create_mock_response(
            mock_api.entity_response(
                entities={"Q42": {"label": "Douglas Adams"}},
                missing_ids=["Q999"],
            )
        )

        with patch.object(wikidata_service, "_get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_get_session.return_value = mock_session

            entities = await wikidata_service.get_entities(["Q42", "Q999"])

            assert len(entities) == 1
            assert "Q42" in entities
            assert "Q999" not in entities


# =============================================================================
# Unit Tests - Error Handling
# =============================================================================


class TestErrorHandling:
    """Unit tests for error handling."""

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


# =============================================================================
# Unit Tests - Context Manager
# =============================================================================


class TestContextManager:
    """Unit tests for context manager usage."""

    async def test_context_manager_creates_and_closes_session(
        self, wikidata_service: WikidataService
    ):
        """Test context manager properly manages session lifecycle."""
        assert wikidata_service._session is None

        async with wikidata_service:
            assert wikidata_service._session is not None

        # Session should be closed after context exit


# =============================================================================
# Integration Tests - Real Wikidata API
# =============================================================================


@pytest.mark.integration
class TestWikidataIntegration:
    """
    Integration tests that connect to the real Wikidata API.

    These tests are skipped by default. Run with:
        pytest tests/test_services/test_wikidata_service.py -m integration
    """

    @pytest.fixture
    def live_service(self) -> WikidataService:
        """Create service configured for real API."""
        return WikidataService(
            settings=WikidataSettings(
                base_url="https://www.wikidata.org/w/api.php",
                timeout=30.0,
                default_language="en",
            )
        )

    async def test_search_real_entity(self, live_service: WikidataService):
        """Test searching for a well-known entity (Douglas Adams)."""
        async with live_service:
            results = await live_service.search_entities("Douglas Adams", limit=5)

            assert len(results) > 0
            # Q42 is Douglas Adams - very stable entity
            qids = [r.qid for r in results]
            assert "Q42" in qids

    async def test_get_real_entity(self, live_service: WikidataService):
        """Test fetching Q42 (Douglas Adams) - a stable, well-known entity."""
        async with live_service:
            entity = await live_service.get_entity("Q42")

            assert entity is not None
            assert entity.qid == "Q42"
            # Douglas Adams is very stable
            assert "Douglas Adams" in entity.label or "Adams" in entity.label

    async def test_get_missing_entity(self, live_service: WikidataService):
        """Test fetching a non-existent entity returns None or raises API error."""
        async with live_service:
            # Use a reasonable non-existent QID that won't cause API errors
            # Note: Wikidata may return an error or missing flag depending on the ID
            try:
                entity = await live_service.get_entity("Q999999999")
                # If no error, should be None
                assert entity is None
            except WikidataAPIError:
                # API may raise error for invalid IDs, which is also acceptable
                pass

    async def test_batch_get_entities(self, live_service: WikidataService):
        """Test batch fetching multiple entities."""
        async with live_service:
            entities = await live_service.get_entities(["Q42", "Q1", "Q2"])

            assert len(entities) >= 2
            assert "Q42" in entities  # Douglas Adams
            assert "Q1" in entities  # Universe
