"""
Wikidata Search API endpoint (stub).

Returns mock data for now - real integration in Phase 6.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()


class WikidataSearchResult(BaseModel):
    """Single Wikidata search result."""
    qid: str = Field(description="Wikidata item ID (e.g., Q12345)")
    label: str = Field(description="Item label")
    description: str | None = Field(default=None, description="Item description")
    aliases: list[str] = Field(default_factory=list, description="Alternative names")


class WikidataSearchResponse(BaseModel):
    """Response for Wikidata search."""
    results: list[WikidataSearchResult]


# Mock data for the stub
MOCK_RESULTS = [
    WikidataSearchResult(
        qid="Q5879",
        label="Johann Wolfgang von Goethe",
        description="German writer and statesman (1749-1832)",
        aliases=["Goethe", "J. W. von Goethe"],
    ),
    WikidataSearchResult(
        qid="Q9438",
        label="Friedrich Schiller",
        description="German poet, philosopher, and playwright (1759-1805)",
        aliases=["Schiller", "Friedrich von Schiller"],
    ),
    WikidataSearchResult(
        qid="Q7200",
        label="Alexander Pushkin",
        description="Russian poet and writer (1799-1837)",
        aliases=["Pushkin", "A. S. Pushkin"],
    ),
]


@router.get("/search", response_model=WikidataSearchResponse)
async def search_wikidata(
    query: str = Query(min_length=1, description="Search query"),
    type: str | None = Query(default=None, description="Entity type filter"),
    limit: int = Query(default=10, ge=1, le=50, description="Max results"),
):
    """
    Search Wikidata for matching entities.

    Note: This is a stub returning mock data. Real Wikidata integration
    will be implemented in Phase 6.
    """
    # Filter mock results based on query (case-insensitive)
    query_lower = query.lower()
    matching = [
        r for r in MOCK_RESULTS
        if query_lower in r.label.lower()
        or query_lower in (r.description or "").lower()
        or any(query_lower in alias.lower() for alias in r.aliases)
    ]

    return WikidataSearchResponse(results=matching[:limit])
