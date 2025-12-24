"""Tests for Task request/response schemas."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.enums import TaskStatus
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)


class TestTaskBase:
    """Tests for TaskBase schema."""

    def test_valid_task_base(self):
        """Test creating valid TaskBase."""
        task = TaskBase(notes="Review notes")
        assert task.notes == "Review notes"

    def test_empty_notes_allowed(self):
        """Test that empty notes is allowed."""
        task = TaskBase()
        assert task.notes is None


class TestTaskCreate:
    """Tests for TaskCreate schema."""

    def test_valid_create(self):
        """Test creating with required fields."""
        task = TaskCreate(
            project_uuid=uuid4(),
            dataset_entry_uuid=uuid4(),
        )
        assert task.notes is None

    def test_create_with_notes(self):
        """Test creating with notes."""
        task = TaskCreate(
            project_uuid=uuid4(),
            dataset_entry_uuid=uuid4(),
            notes="Initial notes",
        )
        assert task.notes == "Initial notes"


class TestTaskUpdate:
    """Tests for TaskUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid."""
        update = TaskUpdate()
        assert update.status is None
        assert update.notes is None

    def test_status_update(self):
        """Test status update."""
        update = TaskUpdate(status=TaskStatus.REVIEWED)
        assert update.status == TaskStatus.REVIEWED

    def test_wikidata_id_pattern(self):
        """Test Wikidata ID must have Q prefix."""
        update = TaskUpdate(accepted_wikidata_id="Q12345")
        assert update.accepted_wikidata_id == "Q12345"

        with pytest.raises(ValidationError):
            TaskUpdate(accepted_wikidata_id="P123")  # Wrong prefix


class TestTaskRead:
    """Tests for TaskRead schema."""

    def test_valid_task_read(self):
        """Test creating TaskRead."""
        now = datetime.now(UTC)
        task = TaskRead(
            uuid=uuid4(),
            project_uuid=uuid4(),
            dataset_entry_uuid=uuid4(),
            status=TaskStatus.AWAITING_REVIEW,
            accepted_wikidata_id=None,
            candidate_count=5,
            highest_score=85,
            processing_started_at=now,
            processing_completed_at=now,
            reviewed_at=None,
            reviewed_by_uuid=None,
            notes=None,
            error_message=None,
            extra_data={},
            created_at=now,
            updated_at=now,
        )
        assert task.candidate_count == 5
        assert task.highest_score == 85
        assert task.status == TaskStatus.AWAITING_REVIEW
