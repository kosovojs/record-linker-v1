"""Tests for AuditLog request/response schemas."""

from uuid import uuid4
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.audit_log import AuditLogCreate, AuditLogRead


class TestAuditLogCreate:
    """Tests for AuditLogCreate schema."""

    def test_valid_create_minimal(self):
        """Test creating with minimal fields."""
        log = AuditLogCreate(
            action="project.created",
            entity_type="project",
        )
        assert log.action == "project.created"
        assert log.user_uuid is None
        assert log.context == {}

    def test_valid_create_full(self):
        """Test creating with all fields."""
        log = AuditLogCreate(
            user_uuid=uuid4(),
            action="candidate.accepted",
            entity_type="match_candidate",
            entity_uuid=uuid4(),
            old_value={"status": "suggested"},
            new_value={"status": "accepted"},
            context={"ip_address": "192.168.1.1", "user_agent": "Mozilla"},
            description="User accepted match candidate",
        )
        assert log.old_value["status"] == "suggested"
        assert log.new_value["status"] == "accepted"

    def test_empty_action_rejected(self):
        """Test that empty action is rejected."""
        with pytest.raises(ValidationError):
            AuditLogCreate(
                action="",
                entity_type="project",
            )


class TestAuditLogRead:
    """Tests for AuditLogRead schema."""

    def test_valid_read(self):
        """Test creating AuditLogRead."""
        now = datetime.utcnow()
        log = AuditLogRead(
            uuid=uuid4(),
            user_uuid=uuid4(),
            action="task.reviewed",
            entity_type="task",
            entity_uuid=uuid4(),
            old_value={"status": "awaiting_review"},
            new_value={"status": "reviewed", "accepted_wikidata_id": "Q12345"},
            context={"request_id": "abc123"},
            description="Task reviewed and matched",
            created_at=now,
        )
        assert log.action == "task.reviewed"
        assert log.new_value["accepted_wikidata_id"] == "Q12345"

    def test_read_with_nulls(self):
        """Test AuditLogRead with null optional fields."""
        now = datetime.utcnow()
        log = AuditLogRead(
            uuid=uuid4(),
            user_uuid=None,
            action="system.startup",
            entity_type="system",
            entity_uuid=None,
            old_value=None,
            new_value=None,
            context={},
            description=None,
            created_at=now,
        )
        assert log.user_uuid is None
        assert log.entity_uuid is None
