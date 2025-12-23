"""
Tests for Dataset API endpoints.
"""

import pytest
from httpx import AsyncClient

from app.schemas.enums import DatasetSourceType


@pytest.mark.asyncio
async def test_list_datasets_empty(client: AsyncClient):
    """Test listing datasets when none exist."""
    response = await client.get("/api/v1/datasets")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_create_dataset(client: AsyncClient):
    """Test creating a new dataset."""
    payload = {
        "name": "Test Dataset",
        "slug": "test-dataset",
        "description": "A test dataset",
        "source_type": DatasetSourceType.WEB_SCRAPE.value,
        "entity_type": "person",
    }

    response = await client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Test Dataset"
    assert data["slug"] == "test-dataset"
    assert data["entity_type"] == "person"
    assert "uuid" in data


@pytest.mark.asyncio
async def test_create_dataset_duplicate_slug(client: AsyncClient):
    """Test creating a dataset with duplicate slug fails."""
    payload = {
        "name": "Dataset 1",
        "slug": "unique-slug",
        "source_type": DatasetSourceType.API.value,
        "entity_type": "person",
    }

    # Create first
    response = await client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 201

    # Try to create duplicate
    payload["name"] = "Dataset 2"
    response = await client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_dataset(client: AsyncClient):
    """Test getting a single dataset."""
    # Create a dataset first
    payload = {
        "name": "Get Test",
        "slug": "get-test",
        "source_type": DatasetSourceType.FILE_IMPORT.value,
        "entity_type": "organization",
    }
    create_response = await client.post("/api/v1/datasets", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    # Get it
    response = await client.get(f"/api/v1/datasets/{created['uuid']}")
    assert response.status_code == 200

    data = response.json()
    assert data["uuid"] == created["uuid"]
    assert data["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_dataset_not_found(client: AsyncClient):
    """Test getting a non-existent dataset returns 404."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/datasets/{fake_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_dataset(client: AsyncClient):
    """Test updating a dataset."""
    # Create
    payload = {
        "name": "Original Name",
        "slug": "original-slug",
        "source_type": DatasetSourceType.MANUAL.value,
        "entity_type": "location",
    }
    create_response = await client.post("/api/v1/datasets", json=payload)
    created = create_response.json()

    # Update
    update_payload = {"name": "Updated Name", "description": "New description"}
    response = await client.patch(
        f"/api/v1/datasets/{created['uuid']}", json=update_payload
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "New description"
    assert data["slug"] == "original-slug"  # Unchanged


@pytest.mark.asyncio
async def test_delete_dataset(client: AsyncClient):
    """Test soft deleting a dataset."""
    # Create
    payload = {
        "name": "To Delete",
        "slug": "to-delete",
        "source_type": DatasetSourceType.WEB_SCRAPE.value,
        "entity_type": "person",
    }
    create_response = await client.post("/api/v1/datasets", json=payload)
    created = create_response.json()

    # Delete
    response = await client.delete(f"/api/v1/datasets/{created['uuid']}")
    assert response.status_code == 204

    # Should be gone from list
    list_response = await client.get("/api/v1/datasets")
    items = list_response.json()["items"]
    uuids = [item["uuid"] for item in items]
    assert created["uuid"] not in uuids
