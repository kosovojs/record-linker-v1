"""
Wikidata API integration service.

Provides async methods for searching and fetching entities from Wikidata.
Uses niquests AsyncSession for HTTP requests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import niquests

from app.core.config import WikidataSettings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class WikidataEntity:
    """Represents a Wikidata entity."""

    qid: str
    label: str
    description: str | None = None
    aliases: list[str] | None = None
    claims: dict[str, Any] | None = None


@dataclass
class WikidataSearchResult:
    """Result from Wikidata entity search."""

    qid: str
    label: str
    description: str | None = None
    aliases: list[str] | None = None


class WikidataServiceError(Exception):
    """Base exception for Wikidata service errors."""

    pass


class WikidataNetworkError(WikidataServiceError):
    """Network error when communicating with Wikidata API."""

    pass


class WikidataAPIError(WikidataServiceError):
    """Wikidata API returned an error response."""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code


class WikidataService:
    """
    Service for interacting with Wikidata API.

    Uses niquests AsyncSession for async HTTP requests.
    """

    def __init__(self, settings: WikidataSettings | None = None):
        self.settings = settings or get_settings().wikidata
        self._session: niquests.AsyncSession | None = None

    async def __aenter__(self) -> "WikidataService":
        """Context manager entry - creates session."""
        self._session = niquests.AsyncSession()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit - closes session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _get_session(self) -> niquests.AsyncSession:
        """Get or create the HTTP session."""
        if self._session is None:
            self._session = niquests.AsyncSession()
        return self._session

    async def _make_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Make an API request to Wikidata.

        Args:
            params: Query parameters for the API call

        Returns:
            JSON response from the API

        Raises:
            WikidataNetworkError: On network/timeout issues
            WikidataAPIError: On API error responses
        """
        session = await self._get_session()

        # Add format parameter
        params = {**params, "format": "json"}

        try:
            response = await session.get(
                self.settings.base_url,
                params=params,
                timeout=self.settings.timeout,
            )
            response.raise_for_status()
            data = response.json()

            # Check for API-level errors
            if "error" in data:
                error = data["error"]
                raise WikidataAPIError(
                    error.get("info", "Unknown error"),
                    error.get("code"),
                )

            return data

        except niquests.exceptions.Timeout as e:
            logger.error(f"Wikidata API timeout: {e}")
            raise WikidataNetworkError(f"Request timed out after {self.settings.timeout}s") from e

        except niquests.exceptions.ConnectionError as e:
            logger.error(f"Wikidata connection error: {e}")
            raise WikidataNetworkError(f"Connection error: {e}") from e

        except niquests.exceptions.RequestException as e:
            logger.error(f"Wikidata request error: {e}")
            raise WikidataNetworkError(f"Request failed: {e}") from e

    async def search_entities(
        self,
        query: str,
        language: str | None = None,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[WikidataSearchResult]:
        """
        Search for Wikidata entities matching a query.

        Uses the wbsearchentities API action.

        Args:
            query: Search term
            language: Language code (default from settings)
            entity_type: Entity type filter ('item', 'property', etc.)
            limit: Maximum number of results (1-50)

        Returns:
            List of search results

        Raises:
            WikidataServiceError: On API or network errors
        """
        if not query or not query.strip():
            return []

        language = language or self.settings.default_language
        limit = max(1, min(50, limit))  # Clamp to valid range

        params = {
            "action": "wbsearchentities",
            "search": query.strip(),
            "language": language,
            "uselang": language,
            "limit": limit,
        }

        if entity_type:
            params["type"] = entity_type

        data = await self._make_request(params)

        results = []
        for item in data.get("search", []):
            results.append(
                WikidataSearchResult(
                    qid=item.get("id", ""),
                    label=item.get("label", ""),
                    description=item.get("description"),
                    aliases=item.get("aliases", []),
                )
            )

        return results

    async def get_entity(
        self,
        qid: str,
        language: str | None = None,
    ) -> WikidataEntity | None:
        """
        Fetch a single Wikidata entity by QID.

        Uses the wbgetentities API action.

        Args:
            qid: Wikidata entity ID (e.g., "Q42")
            language: Language for labels/descriptions

        Returns:
            WikidataEntity or None if not found

        Raises:
            WikidataServiceError: On API or network errors
        """
        if not qid or not qid.strip():
            return None

        language = language or self.settings.default_language
        qid = qid.strip().upper()

        params = {
            "action": "wbgetentities",
            "ids": qid,
            "languages": language,
            "props": "labels|descriptions|aliases|claims",
        }

        data = await self._make_request(params)

        entities = data.get("entities", {})
        entity_data = entities.get(qid)

        if not entity_data or entity_data.get("missing"):
            return None

        # Extract label
        labels = entity_data.get("labels", {})
        label_data = labels.get(language, {})
        label = label_data.get("value", qid)

        # Extract description
        descriptions = entity_data.get("descriptions", {})
        desc_data = descriptions.get(language, {})
        description = desc_data.get("value")

        # Extract aliases
        aliases_data = entity_data.get("aliases", {})
        lang_aliases = aliases_data.get(language, [])
        aliases = [a.get("value") for a in lang_aliases if a.get("value")]

        # Extract claims (simplified - just property IDs and main values)
        claims = entity_data.get("claims", {})

        return WikidataEntity(
            qid=qid,
            label=label,
            description=description,
            aliases=aliases if aliases else None,
            claims=claims if claims else None,
        )

    async def get_entities(
        self,
        qids: list[str],
        language: str | None = None,
    ) -> dict[str, WikidataEntity]:
        """
        Fetch multiple Wikidata entities by QIDs.

        Args:
            qids: List of Wikidata entity IDs
            language: Language for labels/descriptions

        Returns:
            Dict mapping QID to WikidataEntity (missing entities excluded)
        """
        if not qids:
            return {}

        language = language or self.settings.default_language
        qids = [q.strip().upper() for q in qids if q and q.strip()]

        if not qids:
            return {}

        # Wikidata API allows up to 50 entities per request
        params = {
            "action": "wbgetentities",
            "ids": "|".join(qids[:50]),
            "languages": language,
            "props": "labels|descriptions|aliases",
        }

        data = await self._make_request(params)

        results = {}
        entities = data.get("entities", {})

        for qid, entity_data in entities.items():
            if entity_data.get("missing"):
                continue

            labels = entity_data.get("labels", {})
            label_data = labels.get(language, {})
            label = label_data.get("value", qid)

            descriptions = entity_data.get("descriptions", {})
            desc_data = descriptions.get(language, {})
            description = desc_data.get("value")

            aliases_data = entity_data.get("aliases", {})
            lang_aliases = aliases_data.get(language, [])
            aliases = [a.get("value") for a in lang_aliases if a.get("value")]

            results[qid] = WikidataEntity(
                qid=qid,
                label=label,
                description=description,
                aliases=aliases if aliases else None,
            )

        return results

    # TODO: Add caching layer
    # Consider implementing:
    # - In-memory TTL cache for search results
    # - Redis cache for entity data
    # - Cache invalidation strategy


def get_wikidata_service() -> WikidataService:
    """Factory function for WikidataService."""
    return WikidataService()
