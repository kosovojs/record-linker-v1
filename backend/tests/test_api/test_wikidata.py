"""
Tests for Wikidata Search API endpoint (stub).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_wikidata_search_returns_results(client: AsyncClient):
    """Test that search returns mock results matching query."""
    response = await client.get("/api/v1/wikidata/search?query=Goethe")
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert data["results"][0]["qid"] == "Q5879"
    assert "Goethe" in data["results"][0]["label"]


@pytest.mark.asyncio
async def test_wikidata_search_requires_query(client: AsyncClient):
    """Test that query parameter is required."""
    response = await client.get("/api/v1/wikidata/search")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_wikidata_search_no_matches(client: AsyncClient):
    """Test search with no matching results."""
    response = await client.get("/api/v1/wikidata/search?query=xyznonexistent123")
    assert response.status_code == 200

    data = response.json()
    assert data["results"] == []
