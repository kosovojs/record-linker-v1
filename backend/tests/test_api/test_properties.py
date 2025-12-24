"""
Tests for PropertyDefinition API endpoints.
"""

import pytest
from httpx import AsyncClient

from app.schemas.enums import PropertyDataType


@pytest.mark.asyncio
async def test_list_properties_empty(client: AsyncClient):
    """Test listing properties when none exist."""
    response = await client.get("/api/v1/properties")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_property(client: AsyncClient):
    """Test creating a new property definition."""
    payload = {
        "name": "date_of_birth",
        "display_name": "Date of Birth",
        "description": "Person's birth date",
        "data_type": PropertyDataType.DATE.value,
        "is_searchable": True,
        "wikidata_id": "P569",
    }

    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "date_of_birth"
    assert data["display_name"] == "Date of Birth"
    assert data["wikidata_id"] == "P569"
    assert "uuid" in data


@pytest.mark.asyncio
async def test_create_property_duplicate_name(client: AsyncClient):
    """Test creating a property with duplicate name fails."""
    payload = {
        "name": "unique_name",
        "display_name": "Unique Name",
        "data_type": PropertyDataType.TEXT.value,
    }

    # Create first
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 201

    # Try duplicate
    payload["display_name"] = "Different Display"
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_property(client: AsyncClient):
    """Test getting a single property."""
    # Create first
    payload = {
        "name": "full_name",
        "display_name": "Full Name",
        "data_type": PropertyDataType.TEXT.value,
        "is_display_field": True,
    }
    create_response = await client.post("/api/v1/properties", json=payload)
    created = create_response.json()

    # Get it
    response = await client.get(f"/api/v1/properties/{created['uuid']}")
    assert response.status_code == 200
    assert response.json()["name"] == "full_name"


@pytest.mark.asyncio
async def test_get_property_not_found(client: AsyncClient):
    """Test getting non-existent property returns 404."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/properties/{fake_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_property(client: AsyncClient):
    """Test updating a property."""
    # Create
    payload = {
        "name": "country",
        "display_name": "Country",
        "data_type": PropertyDataType.TEXT.value,
    }
    create_response = await client.post("/api/v1/properties", json=payload)
    created = create_response.json()

    # Update
    update_payload = {"display_name": "Country of Origin", "is_searchable": False}
    response = await client.patch(
        f"/api/v1/properties/{created['uuid']}", json=update_payload
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Country of Origin"
    assert response.json()["is_searchable"] is False


@pytest.mark.asyncio
async def test_delete_property(client: AsyncClient):
    """Test soft deleting a property."""
    # Create
    payload = {
        "name": "to_delete_prop",
        "display_name": "To Delete",
        "data_type": PropertyDataType.TEXT.value,
    }
    create_response = await client.post("/api/v1/properties", json=payload)
    created = create_response.json()

    # Delete
    response = await client.delete(f"/api/v1/properties/{created['uuid']}")
    assert response.status_code == 204

    # Should be gone
    get_response = await client.get(f"/api/v1/properties/{created['uuid']}")
    assert get_response.status_code == 404
