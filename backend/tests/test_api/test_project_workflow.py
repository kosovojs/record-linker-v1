"""
Tests for Project Workflow API endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.schemas.enums import CandidateSource, DatasetSourceType


@pytest.fixture
async def project_workflow_setup(client: AsyncClient) -> dict:
    """Create dataset, entries, and project for workflow tests."""
    unique_id = str(uuid.uuid4())[:8]

    # Create dataset
    dataset_payload = {
        "name": f"Workflow Test Dataset {unique_id}",
        "slug": f"workflow-test-dataset-{unique_id}",
        "source_type": DatasetSourceType.WEB_SCRAPE.value,
        "entity_type": "person",
    }
    dataset_resp = await client.post("/api/v1/datasets", json=dataset_payload)
    dataset = dataset_resp.json()

    # Create multiple entries
    entries_payload = [
        {"dataset_uuid": dataset["uuid"], "external_id": f"entry-{unique_id}-1"},
        {"dataset_uuid": dataset["uuid"], "external_id": f"entry-{unique_id}-2"},
        {"dataset_uuid": dataset["uuid"], "external_id": f"entry-{unique_id}-3"},
    ]
    entries_resp = await client.post(
        f"/api/v1/datasets/{dataset['uuid']}/entries", json=entries_payload
    )
    entries = entries_resp.json()

    # Create project
    project_payload = {
        "name": f"Workflow Test Project {unique_id}",
        "dataset_uuid": dataset["uuid"],
    }
    project_resp = await client.post("/api/v1/projects", json=project_payload)
    project = project_resp.json()

    return {"dataset": dataset, "entries": entries, "project": project}


@pytest.mark.asyncio
async def test_start_project_requires_entries_or_all_flag(
    client: AsyncClient, project_workflow_setup: dict
):
    """Test that start requires entry_uuids or all_entries flag."""
    project = project_workflow_setup["project"]

    # Empty request should fail
    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/start", json={}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_start_project_with_all_entries(
    client: AsyncClient, project_workflow_setup: dict
):
    """Test starting project with all_entries flag."""
    project = project_workflow_setup["project"]

    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/start",
        json={"all_entries": True}
    )
    assert response.status_code == 202

    data = response.json()
    assert data["tasks_created"] == 3
    assert data["project_status"] == "pending_search"
    assert data["message"] == "Project started"


@pytest.mark.asyncio
async def test_start_project_with_specific_entries(
    client: AsyncClient, project_workflow_setup: dict
):
    """Test starting project with specific entry UUIDs."""
    project = project_workflow_setup["project"]
    entries = project_workflow_setup["entries"]

    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/start",
        json={"entry_uuids": [entries[0]["uuid"], entries[1]["uuid"]]}
    )
    assert response.status_code == 202

    data = response.json()
    assert data["tasks_created"] == 2


@pytest.mark.asyncio
async def test_get_project_stats(client: AsyncClient, project_workflow_setup: dict):
    """Test getting project statistics."""
    project = project_workflow_setup["project"]

    # Start project first
    await client.post(
        f"/api/v1/projects/{project['uuid']}/start",
        json={"all_entries": True}
    )

    response = await client.get(f"/api/v1/projects/{project['uuid']}/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["total_tasks"] == 3
    assert "by_status" in data
    assert data["by_status"].get("new", 0) == 3
    assert data["candidates"]["total"] == 0
    assert data["progress_percent"] == 0.0


@pytest.mark.asyncio
async def test_get_approved_matches_empty(
    client: AsyncClient, project_workflow_setup: dict
):
    """Test approved matches when none exist."""
    project = project_workflow_setup["project"]

    response = await client.get(f"/api/v1/projects/{project['uuid']}/approved-matches")
    assert response.status_code == 200

    data = response.json()
    assert data["matches"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_rerun_requires_criteria_or_uuids(
    client: AsyncClient, project_workflow_setup: dict
):
    """Test that rerun requires criteria or task_uuids."""
    project = project_workflow_setup["project"]

    response = await client.post(
        f"/api/v1/projects/{project['uuid']}/rerun", json={}
    )
    assert response.status_code == 400
