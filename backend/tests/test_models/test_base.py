"""Tests for BaseTableModel and model inheritance."""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.base import BaseTableModel, utc_now
from sqlmodel import SQLModel


class TestUtcNow:
    """Test the utc_now helper function."""

    def test_returns_datetime(self):
        """Test utc_now returns a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_has_timezone(self):
        """Test utc_now returns timezone-aware datetime."""
        result = utc_now()
        assert result.tzinfo is not None


class TestBaseTableModel:
    """Test BaseTableModel base class features."""

    def test_is_sqlmodel_subclass(self):
        """Test BaseTableModel inherits from SQLModel."""
        assert issubclass(BaseTableModel, SQLModel)

    def test_has_id_field(self):
        """Test BaseTableModel has id field defined."""
        fields = BaseTableModel.model_fields
        assert "id" in fields

    def test_has_uuid_field(self):
        """Test BaseTableModel has uuid field with UUID type."""
        fields = BaseTableModel.model_fields
        assert "uuid" in fields

    def test_has_timestamp_fields(self):
        """Test BaseTableModel has created_at and updated_at."""
        fields = BaseTableModel.model_fields
        assert "created_at" in fields
        assert "updated_at" in fields

    def test_has_soft_delete_field(self):
        """Test BaseTableModel has deleted_at for soft delete."""
        fields = BaseTableModel.model_fields
        assert "deleted_at" in fields


class TestSoftDeleteMixin:
    """Test soft delete functionality in BaseTableModel."""

    def test_is_deleted_false_when_deleted_at_none(self):
        """Test is_deleted returns False when deleted_at is None."""
        # Create a concrete model instance for testing
        from app.models.user import User

        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        assert user.deleted_at is None
        assert user.is_deleted is False

    def test_is_deleted_true_when_deleted_at_set(self):
        """Test is_deleted returns True when deleted_at is set."""
        from app.models.user import User

        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        user.deleted_at = utc_now()
        assert user.is_deleted is True

    def test_soft_delete_sets_deleted_at(self):
        """Test soft_delete() method sets deleted_at."""
        from app.models.user import User

        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        assert user.deleted_at is None
        user.soft_delete()
        assert user.deleted_at is not None
        assert user.is_deleted is True

    def test_restore_clears_deleted_at(self):
        """Test restore() method clears deleted_at."""
        from app.models.user import User

        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        user.soft_delete()
        assert user.is_deleted is True
        user.restore()
        assert user.deleted_at is None
        assert user.is_deleted is False


class TestModelUUID:
    """Test UUID generation for models."""

    def test_uuid_auto_generated(self):
        """Test UUID is auto-generated when not provided."""
        from app.models.user import User

        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        assert user.uuid is not None
        assert isinstance(user.uuid, uuid.UUID)

    def test_uuid_unique_per_instance(self):
        """Test each instance gets a unique UUID."""
        from app.models.user import User

        user1 = User(email="test1@example.com", display_name="User 1")
        user2 = User(email="test2@example.com", display_name="User 2")
        assert user1.uuid != user2.uuid


class TestModelDefaults:
    """Test default values are set correctly."""

    def test_user_defaults(self):
        """Test User model has correct defaults."""
        from app.models.user import User
        from app.schemas.jsonb_types import UserSettings

        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        assert user.role == "user"
        assert user.status == "active"
        assert user.password_hash is None
        # Settings now uses typed schema defaults
        assert "notifications" in user.settings
        assert "ui" in user.settings
        # Verify it parses back to typed model
        typed_settings = user.get_settings()
        assert isinstance(typed_settings, UserSettings)

    def test_project_defaults(self):
        """Test Project model has correct defaults."""
        from app.models.project import Project
        from app.schemas.jsonb_types import ProjectConfig

        project = Project(
            dataset_id=1,
            owner_id=1,
            name="Test Project",
        )
        assert project.status == "draft"
        assert project.task_count == 0
        assert project.tasks_completed == 0
        # Config now uses typed schema defaults
        assert "matching_weights" in project.config
        # Verify it parses back to typed model
        typed_config = project.get_config()
        assert isinstance(typed_config, ProjectConfig)

    def test_task_defaults(self):
        """Test Task model has correct defaults."""
        from app.models.task import Task

        task = Task(
            project_id=1,
            dataset_entry_id=1,
        )
        assert task.status == "new"
        assert task.candidate_count == 0
        assert task.accepted_candidate_id is None
        assert task.accepted_wikidata_id is None

    def test_candidate_defaults(self):
        """Test MatchCandidate model has correct defaults."""
        from app.models.match_candidate import MatchCandidate

        candidate = MatchCandidate(
            task_id=1,
            wikidata_id="Q12345",
            score=85,
            source="automated_search",
        )
        assert candidate.status == "suggested"
        assert candidate.tags == []
        assert candidate.notes is None
