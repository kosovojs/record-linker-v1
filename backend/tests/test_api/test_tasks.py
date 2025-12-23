"""
Tests for Task API endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.schemas.enums import DatasetSourceType


@pytest.fixture
async def test_setup_for_tasks(client: AsyncClient) -> dict:
    """Create dataset, entry, and project for task tests."""
    unique_id = str(uuid.uuid4())[:8]

    # Create dataset
    dataset_payload = {
        "name": f"Task Test Dataset {unique_id}",
        "slug": f"task-test-dataset-{unique_id}",
        "source_type": DatasetSourceType.WEB_SCRAPE.value,
        "entity_type": "person",
    }
    dataset_resp = await client.post("/api/v1/datasets", json=dataset_payload)
    dataset = dataset_resp.json()

    # Create entry
    entry_payload = [
        {"dataset_uuid": dataset["uuid"], "external_id": f"entry-{unique_id}"},
    ]
    entry_resp = await client.post(
        f"/api/v1/datasets/{dataset['uuid']}/entries", json=entry_payload
    )
    entry = entry_resp.json()[0]

    # Create project
    project_payload = {
        "name": f"Task Test Project {unique_id}",
        "dataset_uuid": dataset["uuid"],
    }
    project_resp = await client.post("/api/v1/projects", json=project_payload)
    project = project_resp.json()

    return {"dataset": dataset, "entry": entry, "project": project}


@pytest.mark.asyncio
async def test_list_tasks_empty(client: AsyncClient, test_setup_for_tasks: dict):
    """Test listing tasks when none exist."""
    project = test_setup_for_tasks["project"]
    response = await client.get(f"/api/v1/projects/{project['uuid']}/tasks")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, test_setup_for_tasks: dict):
    """Test creating a task."""
    project = test_setup_for_tasks["project"]
    entry = test_setup_for_tasks["entry"]

    payload = {
        "project_uuid": project["uuid"],
        "dataset_entry_uuid": entry["uuid"],
    }

    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=payload
    )
    assert response.status_code == 201

    data = response.json()
    assert data["project_uuid"] == project["uuid"]
    assert data["dataset_entry_uuid"] == entry["uuid"]
    assert data["status"] == "new"


@pytest.mark.asyncio
async def test_create_task_duplicate(client: AsyncClient, test_setup_for_tasks: dict):
    """Test that duplicate project/entry combo fails."""
    project = test_setup_for_tasks["project"]
    entry = test_setup_for_tasks["entry"]

    payload = {
        "project_uuid": project["uuid"],
        "dataset_entry_uuid": entry["uuid"],
    }

    # Create first
    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=payload
    )
    assert response.status_code == 201

    # Try duplicate
    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=payload
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, test_setup_for_tasks: dict):
    """Test getting a single task."""
    project = test_setup_for_tasks["project"]
    entry = test_setup_for_tasks["entry"]

    # Create task
    payload = {
        "project_uuid": project["uuid"],
        "dataset_entry_uuid": entry["uuid"],
    }
    create_resp = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=payload
    )
    created = create_resp.json()

    # Get via nested route
    response = await client.get(
        f"/api/v1/projects/{project['uuid']}/tasks/{created['uuid']}"
    )
    assert response.status_code == 200
    assert response.json()["uuid"] == created["uuid"]


@pytest.mark.asyncio
async def test_get_task_by_uuid_alias(client: AsyncClient, test_setup_for_tasks: dict):
    """Test getting task via direct /tasks/{uuid} alias."""
    project = test_setup_for_tasks["project"]
    entry = test_setup_for_tasks["entry"]

    # Create task
    payload = {
        "project_uuid": project["uuid"],
        "dataset_entry_uuid": entry["uuid"],
    }
    create_resp = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=payload
    )
    created = create_resp.json()

    # Get via alias
    response = await client.get(f"/api/v1/tasks/{created['uuid']}")
    assert response.status_code == 200
    assert response.json()["uuid"] == created["uuid"]
    assert response.json()["project_uuid"] == project["uuid"]


@pytest.mark.asyncio
async def test_skip_task(client: AsyncClient, test_setup_for_tasks: dict):
    """Test skipping a task."""
    project = test_setup_for_tasks["project"]
    entry = test_setup_for_tasks["entry"]

    # Create task
    payload = {
        "project_uuid": project["uuid"],
        "dataset_entry_uuid": entry["uuid"],
    }
    create_resp = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=payload
    )
    created = create_resp.json()

    # Skip
    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks/{created['uuid']}/skip"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "skipped"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, test_setup_for_tasks: dict):
    """Test soft deleting a task."""
    project = test_setup_for_tasks["project"]
    entry = test_setup_for_tasks["entry"]

    # Create task
    payload = {
        "project_uuid": project["uuid"],
        "dataset_entry_uuid": entry["uuid"],
    }
    create_resp = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=payload
    )
    created = create_resp.json()

    # Delete
    response = await client.delete(
        f"/api/v1/projects/{project['uuid']}/tasks/{created['uuid']}"
    )
    assert response.status_code == 204

    # Should be gone
    get_resp = await client.get(
        f"/api/v1/projects/{project['uuid']}/tasks/{created['uuid']}"
    )
    assert get_resp.status_code == 404
