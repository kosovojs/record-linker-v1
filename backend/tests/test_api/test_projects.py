"""
Tests for Project API endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.schemas.enums import DatasetSourceType


@pytest.fixture
async def test_dataset(client: AsyncClient) -> dict:
    """Create a test dataset for project tests."""
    unique_id = str(uuid.uuid4())[:8]
    payload = {
        "name": f"Project Test Dataset {unique_id}",
        "slug": f"project-test-dataset-{unique_id}",
        "source_type": DatasetSourceType.WEB_SCRAPE.value,
        "entity_type": "person",
    }
    response = await client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient):
    """Test listing projects when none exist."""
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, test_dataset: dict):
    """Test creating a new project."""
    payload = {
        "name": "Test Project",
        "description": "A test project for matching",
        "dataset_uuid": test_dataset["uuid"],
    }

    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Test Project"
    assert data["dataset_uuid"] == test_dataset["uuid"]
    assert data["status"] == "draft"
    assert "uuid" in data


@pytest.mark.asyncio
async def test_create_project_invalid_dataset(client: AsyncClient):
    """Test creating project with non-existent dataset fails."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    payload = {
        "name": "Bad Project",
        "dataset_uuid": fake_uuid,
    }

    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 404
    assert "Dataset" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, test_dataset: dict):
    """Test getting a single project."""
    # Create project
    payload = {
        "name": "Get Test Project",
        "dataset_uuid": test_dataset["uuid"],
    }
    create_response = await client.post("/api/v1/projects", json=payload)
    created = create_response.json()

    # Get it
    response = await client.get(f"/api/v1/projects/{created['uuid']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test Project"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    """Test getting non-existent project returns 404."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/projects/{fake_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, test_dataset: dict):
    """Test updating a project."""
    # Create
    payload = {
        "name": "Original Project Name",
        "dataset_uuid": test_dataset["uuid"],
    }
    create_response = await client.post("/api/v1/projects", json=payload)
    created = create_response.json()

    # Update
    update_payload = {"name": "Updated Project Name", "description": "New description"}
    response = await client.patch(
        f"/api/v1/projects/{created['uuid']}", json=update_payload
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project Name"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, test_dataset: dict):
    """Test soft deleting a project."""
    # Create
    payload = {
        "name": "To Delete Project",
        "dataset_uuid": test_dataset["uuid"],
    }
    create_response = await client.post("/api/v1/projects", json=payload)
    created = create_response.json()

    # Delete
    response = await client.delete(f"/api/v1/projects/{created['uuid']}")
    assert response.status_code == 204

    # Should be gone
    get_response = await client.get(f"/api/v1/projects/{created['uuid']}")
    assert get_response.status_code == 404
