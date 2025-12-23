"""Tests for enum definitions."""


from app.schemas.enums import (
    CandidateSource,
    CandidateStatus,
    ProjectStatus,
    TaskStatus,
    UserRole,
    UserStatus,
)


class TestEnumValues:
    """Test enum values are correctly defined."""

    def test_user_role_values(self):
        """Test UserRole enum has expected values."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.USER == "user"
        assert UserRole.VIEWER == "viewer"
        assert len(UserRole) == 3

    def test_user_status_values(self):
        """Test UserStatus enum has expected values."""
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.BLOCKED == "blocked"
        assert len(UserStatus) == 4

    def test_project_status_values(self):
        """Test ProjectStatus enum has expected values."""
        assert ProjectStatus.DRAFT == "draft"
        assert ProjectStatus.ACTIVE == "active"
        assert ProjectStatus.COMPLETED == "completed"
        assert ProjectStatus.ARCHIVED == "archived"
        assert len(ProjectStatus) == 11

    def test_task_status_values(self):
        """Test TaskStatus enum has expected values."""
        assert TaskStatus.NEW == "new"
        assert TaskStatus.PROCESSING == "processing"
        assert TaskStatus.REVIEWED == "reviewed"
        assert len(TaskStatus) == 10

    def test_candidate_status_values(self):
        """Test CandidateStatus enum has expected values."""
        assert CandidateStatus.SUGGESTED == "suggested"
        assert CandidateStatus.ACCEPTED == "accepted"
        assert CandidateStatus.REJECTED == "rejected"
        assert len(CandidateStatus) == 3

    def test_candidate_source_values(self):
        """Test CandidateSource enum has expected values."""
        assert CandidateSource.AUTOMATED_SEARCH == "automated_search"
        assert CandidateSource.MANUAL == "manual"
        assert len(CandidateSource) == 5


class TestEnumSerialization:
    """Test enums serialize correctly to strings."""

    def test_enum_string_conversion(self):
        """Test enums convert to strings properly."""
        assert str(TaskStatus.NEW) == "new"
        assert str(UserRole.ADMIN) == "admin"

    def test_enum_json_serializable(self):
        """Test enums are JSON serializable."""
        import json

        data = {
            "status": TaskStatus.PROCESSING,
            "role": UserRole.USER,
        }
        # StrEnum should serialize to string automatically
        serialized = json.dumps(data)
        assert '"processing"' in serialized
        assert '"user"' in serialized
