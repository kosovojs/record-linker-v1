"""
Tests for Candidate API endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.schemas.enums import CandidateSource, CandidateStatus, DatasetSourceType


@pytest.fixture
async def test_setup_for_candidates(client: AsyncClient) -> dict:
    """Create dataset, entry, project, and task for candidate tests."""
    unique_id = str(uuid.uuid4())[:8]

    # Create dataset
    dataset_payload = {
        "name": f"Candidate Test Dataset {unique_id}",
        "slug": f"candidate-test-dataset-{unique_id}",
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
        "name": f"Candidate Test Project {unique_id}",
        "dataset_uuid": dataset["uuid"],
    }
    project_resp = await client.post("/api/v1/projects", json=project_payload)
    project = project_resp.json()

    # Create task
    task_payload = {
        "project_uuid": project["uuid"],
        "dataset_entry_uuid": entry["uuid"],
    }
    task_resp = await client.post(
        f"/api/v1/projects/{project['uuid']}/tasks", json=task_payload
    )
    task = task_resp.json()

    return {"dataset": dataset, "entry": entry, "project": project, "task": task}


@pytest.mark.asyncio
async def test_list_candidates_empty(client: AsyncClient, test_setup_for_candidates: dict):
    """Test listing candidates when none exist."""
    task = test_setup_for_candidates["task"]
    response = await client.get(f"/api/v1/tasks/{task['uuid']}/candidates")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_candidates_bulk(client: AsyncClient, test_setup_for_candidates: dict):
    """Test bulk creating candidates."""
    task = test_setup_for_candidates["task"]

    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q12345",
                "score": 85,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q67890",
                "score": 72,
                "source": CandidateSource.MANUAL.value,
            },
        ]
    }

    response = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    assert response.status_code == 201

    data = response.json()
    assert len(data) == 2
    assert data[0]["wikidata_id"] == "Q12345"
    assert data[0]["score"] == 85
    assert data[0]["status"] == CandidateStatus.SUGGESTED.value
    assert data[1]["wikidata_id"] == "Q67890"


@pytest.mark.asyncio
async def test_get_candidate(client: AsyncClient, test_setup_for_candidates: dict):
    """Test getting a single candidate."""
    task = test_setup_for_candidates["task"]

    # Create candidate
    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q11111",
                "score": 90,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
        ]
    }
    create_resp = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    created = create_resp.json()[0]

    # Get it
    response = await client.get(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}"
    )
    assert response.status_code == 200
    assert response.json()["uuid"] == created["uuid"]
    assert response.json()["wikidata_id"] == "Q11111"


@pytest.mark.asyncio
async def test_update_candidate(client: AsyncClient, test_setup_for_candidates: dict):
    """Test updating a candidate."""
    task = test_setup_for_candidates["task"]

    # Create candidate
    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q22222",
                "score": 80,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
        ]
    }
    create_resp = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    created = create_resp.json()[0]

    # Update notes
    update_payload = {"notes": "Looks like a good match"}
    response = await client.patch(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}", json=update_payload
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Looks like a good match"


@pytest.mark.asyncio
async def test_delete_candidate(client: AsyncClient, test_setup_for_candidates: dict):
    """Test soft deleting a candidate."""
    task = test_setup_for_candidates["task"]

    # Create candidate
    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q33333",
                "score": 75,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
        ]
    }
    create_resp = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    created = create_resp.json()[0]

    # Delete
    response = await client.delete(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}"
    )
    assert response.status_code == 204

    # Should be gone
    get_resp = await client.get(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}"
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_accept_candidate(client: AsyncClient, test_setup_for_candidates: dict):
    """Test accepting a candidate."""
    task = test_setup_for_candidates["task"]

    # Create candidate
    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q44444",
                "score": 95,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
        ]
    }
    create_resp = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    created = create_resp.json()[0]

    # Accept
    response = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}/accept"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["candidate"]["status"] == CandidateStatus.ACCEPTED.value
    assert data["task"]["status"] == "reviewed"
    assert data["task"]["accepted_wikidata_id"] == "Q44444"


@pytest.mark.asyncio
async def test_reject_candidate(client: AsyncClient, test_setup_for_candidates: dict):
    """Test rejecting a candidate."""
    task = test_setup_for_candidates["task"]

    # Create candidate
    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q55555",
                "score": 60,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
        ]
    }
    create_resp = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    created = create_resp.json()[0]

    # Reject
    response = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}/reject"
    )
    assert response.status_code == 200
    assert response.json()["status"] == CandidateStatus.REJECTED.value


@pytest.mark.asyncio
async def test_cannot_accept_already_rejected(
    client: AsyncClient, test_setup_for_candidates: dict
):
    """Test that we can't accept an already rejected candidate."""
    task = test_setup_for_candidates["task"]

    # Create candidate
    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q66666",
                "score": 70,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
        ]
    }
    create_resp = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    created = create_resp.json()[0]

    # Reject first
    await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}/reject"
    )

    # Try to accept - should fail
    response = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates/{created['uuid']}/accept"
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_bulk_update_candidates(client: AsyncClient, test_setup_for_candidates: dict):
    """Test bulk updating candidates."""
    task = test_setup_for_candidates["task"]

    # Create multiple candidates
    payload = {
        "candidates": [
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q77777",
                "score": 50,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
            {
                "task_uuid": task["uuid"],
                "wikidata_id": "Q88888",
                "score": 55,
                "source": CandidateSource.AUTOMATED_SEARCH.value,
            },
        ]
    }
    create_resp = await client.post(
        f"/api/v1/tasks/{task['uuid']}/candidates", json=payload
    )
    created = create_resp.json()

    # Bulk reject
    bulk_payload = {
        "candidate_uuids": [c["uuid"] for c in created],
        "updates": {"status": CandidateStatus.REJECTED.value},
    }
    response = await client.patch(
        f"/api/v1/tasks/{task['uuid']}/candidates/bulk", json=bulk_payload
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert all(c["status"] == CandidateStatus.REJECTED.value for c in data)
