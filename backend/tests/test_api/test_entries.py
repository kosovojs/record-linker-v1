"""
Tests for DatasetEntry API endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.schemas.enums import DatasetSourceType


@pytest.fixture
async def test_dataset_for_entries(client: AsyncClient) -> dict:
    """Create a test dataset for entry tests."""
    unique_id = str(uuid.uuid4())[:8]
    payload = {
        "name": f"Entry Test Dataset {unique_id}",
        "slug": f"entry-test-dataset-{unique_id}",
        "source_type": DatasetSourceType.WEB_SCRAPE.value,
        "entity_type": "person",
    }
    response = await client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_list_entries_empty(client: AsyncClient, test_dataset_for_entries: dict):
    """Test listing entries when none exist."""
    response = await client.get(
        f"/api/v1/datasets/{test_dataset_for_entries['uuid']}/entries"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_entries_bulk(client: AsyncClient, test_dataset_for_entries: dict):
    """Test creating entries in bulk."""
    dataset_uuid = test_dataset_for_entries["uuid"]
    payload = [
        {
            "dataset_uuid": dataset_uuid,
            "external_id": "ext-001",
            "display_name": "John Doe",
        },
        {
            "dataset_uuid": dataset_uuid,
            "external_id": "ext-002",
            "display_name": "Jane Smith",
        },
    ]

    response = await client.post(
        f"/api/v1/datasets/{dataset_uuid}/entries", json=payload
    )
    assert response.status_code == 201

    data = response.json()
    assert len(data) == 2
    assert data[0]["external_id"] == "ext-001"
    assert data[1]["external_id"] == "ext-002"


@pytest.mark.asyncio
async def test_create_entry_duplicate_external_id(
    client: AsyncClient, test_dataset_for_entries: dict
):
    """Test that duplicate external_id in same dataset fails."""
    dataset_uuid = test_dataset_for_entries["uuid"]
    payload = [
        {"dataset_uuid": dataset_uuid, "external_id": "duplicate-id"},
    ]

    # Create first
    response = await client.post(
        f"/api/v1/datasets/{dataset_uuid}/entries", json=payload
    )
    assert response.status_code == 201

    # Try duplicate
    response = await client.post(
        f"/api/v1/datasets/{dataset_uuid}/entries", json=payload
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_entry(client: AsyncClient, test_dataset_for_entries: dict):
    """Test getting a single entry."""
    dataset_uuid = test_dataset_for_entries["uuid"]
    payload = [
        {"dataset_uuid": dataset_uuid, "external_id": "get-test"},
    ]
    create_response = await client.post(
        f"/api/v1/datasets/{dataset_uuid}/entries", json=payload
    )
    created = create_response.json()[0]

    response = await client.get(
        f"/api/v1/datasets/{dataset_uuid}/entries/{created['uuid']}"
    )
    assert response.status_code == 200
    assert response.json()["external_id"] == "get-test"


@pytest.mark.asyncio
async def test_update_entry(client: AsyncClient, test_dataset_for_entries: dict):
    """Test updating an entry."""
    dataset_uuid = test_dataset_for_entries["uuid"]
    payload = [
        {"dataset_uuid": dataset_uuid, "external_id": "update-test"},
    ]
    create_response = await client.post(
        f"/api/v1/datasets/{dataset_uuid}/entries", json=payload
    )
    created = create_response.json()[0]

    update_payload = {"display_name": "Updated Name"}
    response = await client.patch(
        f"/api/v1/datasets/{dataset_uuid}/entries/{created['uuid']}",
        json=update_payload,
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_entry(client: AsyncClient, test_dataset_for_entries: dict):
    """Test soft deleting an entry."""
    dataset_uuid = test_dataset_for_entries["uuid"]
    payload = [
        {"dataset_uuid": dataset_uuid, "external_id": "delete-test"},
    ]
    create_response = await client.post(
        f"/api/v1/datasets/{dataset_uuid}/entries", json=payload
    )
    created = create_response.json()[0]

    response = await client.delete(
        f"/api/v1/datasets/{dataset_uuid}/entries/{created['uuid']}"
    )
    assert response.status_code == 204

    # Should be gone
    get_response = await client.get(
        f"/api/v1/datasets/{dataset_uuid}/entries/{created['uuid']}"
    )
    assert get_response.status_code == 404
