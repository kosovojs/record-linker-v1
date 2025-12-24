"""Tests for Project request/response schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.enums import ProjectStatus
from app.schemas.jsonb_types import ProjectConfig
from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)


class TestProjectBase:
    """Tests for ProjectBase schema."""

    def test_valid_project_base(self):
        """Test creating valid ProjectBase."""
        project = ProjectBase(name="EP Players - Batch 1")
        assert project.name == "EP Players - Batch 1"
        assert project.description is None

    def test_empty_name_rejected(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError):
            ProjectBase(name="")


class TestProjectCreate:
    """Tests for ProjectCreate schema."""

    def test_valid_create_minimal(self):
        """Test creating with minimal fields."""
        project = ProjectCreate(
            name="Test Project",
            dataset_uuid=uuid4(),
        )
        assert project.owner_uuid is None
        assert project.config is None

    def test_valid_create_full(self):
        """Test creating with all fields."""
        config = ProjectConfig(auto_accept_threshold=90)
        project = ProjectCreate(
            name="Full Project",
            description="A complete project",
            dataset_uuid=uuid4(),
            owner_uuid=uuid4(),
            config=config,
        )
        assert project.config.auto_accept_threshold == 90


class TestProjectUpdate:
    """Tests for ProjectUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid."""
        update = ProjectUpdate()
        assert update.name is None
        assert update.status is None

    def test_partial_update(self):
        """Test partial update."""
        update = ProjectUpdate(
            status=ProjectStatus.ACTIVE,
        )
        assert update.status == ProjectStatus.ACTIVE

    def test_config_update(self):
        """Test updating config."""
        config = ProjectConfig(auto_reject_threshold=30)
        update = ProjectUpdate(config=config)
        assert update.config.auto_reject_threshold == 30


class TestProjectRead:
    """Tests for ProjectRead schema."""

    def test_valid_project_read(self):
        """Test creating ProjectRead."""
        now = datetime.utcnow()
        project = ProjectRead(
            uuid=uuid4(),
            dataset_uuid=uuid4(),
            owner_uuid=uuid4(),
            name="Test Project",
            description="Description",
            status=ProjectStatus.DRAFT,
            task_count=100,
            tasks_completed=50,
            tasks_with_candidates=75,
            config={},
            started_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        assert project.task_count == 100
        assert project.status == ProjectStatus.DRAFT
