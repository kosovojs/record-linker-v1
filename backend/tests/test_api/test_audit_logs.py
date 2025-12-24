"""
Tests for Audit Log API endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_audit_logs_empty(client: AsyncClient):
    """Test listing audit logs with no entries."""
    response = await client.get("/api/v1/audit-logs")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_get_audit_log_not_found(client: AsyncClient):
    """Test getting a non-existent audit log."""
    fake_uuid = str(uuid.uuid4())
    response = await client.get(f"/api/v1/audit-logs/{fake_uuid}")
    assert response.status_code == 404
