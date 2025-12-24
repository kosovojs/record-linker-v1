"""
Wikidata Search API endpoint.

Uses WikidataService for real Wikidata API integration.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from app.services.wikidata_service import (
    WikidataService,
    WikidataServiceError,
    get_wikidata_service,
)

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


@router.get("/search", response_model=WikidataSearchResponse)
async def search_wikidata(
    query: str = Query(
        min_length=1,
        description="The search string to look for in Wikidata",
        examples=["Douglas Adams"],
    ),
    type: str | None = Query(
        default=None,
        description="Filter by Wikidata entity type (e.g., item, property)",
        examples=["item"],
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return",
        examples=[5],
    ),
    language: str = Query(
        default="en",
        description="ISO language code for search and labels",
        examples=["de"],
    ),
):
    """
    Search Wikidata for matching entities.

    Uses the real Wikidata API via wbsearchentities action.
    """
    service = get_wikidata_service()

    try:
        async with service:
            results = await service.search_entities(
                query=query,
                entity_type=type,
                limit=limit,
                language=language,
            )
    except WikidataServiceError as e:
        raise HTTPException(status_code=502, detail=f"Wikidata API error: {e}") from e

    return WikidataSearchResponse(
        results=[
            WikidataSearchResult(
                qid=r.qid,
                label=r.label,
                description=r.description,
                aliases=r.aliases or [],
            )
            for r in results
        ]
    )


@router.get("/entity/{qid}")
async def get_wikidata_entity(
    qid: str = Path(
        ...,
        description="The Wikidata item ID (must start with 'Q')",
        examples=["Q42"],
    ),
    language: str = Query(
        default="en",
        description="ISO language code for entity labels",
        examples=["fr"],
    ),
):
    """
    Get a single Wikidata entity by QID.
    """
    service = get_wikidata_service()

    try:
        async with service:
            entity = await service.get_entity(qid=qid, language=language)
    except WikidataServiceError as e:
        raise HTTPException(status_code=502, detail=f"Wikidata API error: {e}") from e

    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity {qid} not found")

    return {
        "qid": entity.qid,
        "label": entity.label,
        "description": entity.description,
        "aliases": entity.aliases or [],
    }
