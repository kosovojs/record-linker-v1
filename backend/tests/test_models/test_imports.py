"""Tests for model imports and relationships."""


class TestModelImports:
    """Test that all models can be imported correctly."""

    def test_import_base_model(self):
        """Test BaseTableModel can be imported."""
        from app.models import BaseTableModel

        assert BaseTableModel is not None

    def test_import_user(self):
        """Test User model can be imported."""
        from app.models import User

        assert User is not None
        assert User.__tablename__ == "users"

    def test_import_dataset(self):
        """Test Dataset model can be imported."""
        from app.models import Dataset

        assert Dataset is not None
        assert Dataset.__tablename__ == "datasets"

    def test_import_property_definition(self):
        """Test PropertyDefinition model can be imported."""
        from app.models import PropertyDefinition

        assert PropertyDefinition is not None
        assert PropertyDefinition.__tablename__ == "property_definitions"

    def test_import_dataset_entry(self):
        """Test DatasetEntry model can be imported."""
        from app.models import DatasetEntry

        assert DatasetEntry is not None
        assert DatasetEntry.__tablename__ == "dataset_entries"

    def test_import_dataset_entry_property(self):
        """Test DatasetEntryProperty model can be imported."""
        from app.models import DatasetEntryProperty

        assert DatasetEntryProperty is not None
        assert DatasetEntryProperty.__tablename__ == "dataset_entry_properties"

    def test_import_project(self):
        """Test Project model can be imported."""
        from app.models import Project

        assert Project is not None
        assert Project.__tablename__ == "projects"

    def test_import_task(self):
        """Test Task model can be imported."""
        from app.models import Task

        assert Task is not None
        assert Task.__tablename__ == "tasks"

    def test_import_match_candidate(self):
        """Test MatchCandidate model can be imported."""
        from app.models import MatchCandidate

        assert MatchCandidate is not None
        assert MatchCandidate.__tablename__ == "match_candidates"

    def test_import_audit_log(self):
        """Test AuditLog model can be imported."""
        from app.models import AuditLog

        assert AuditLog is not None
        assert AuditLog.__tablename__ == "audit_logs"


class TestModelInheritance:
    """Test model inheritance from BaseTableModel."""

    def test_user_inherits_base(self):
        """Test User inherits from BaseTableModel."""
        from app.models import BaseTableModel, User

        assert issubclass(User, BaseTableModel)

    def test_dataset_inherits_base(self):
        """Test Dataset inherits from BaseTableModel."""
        from app.models import BaseTableModel, Dataset

        assert issubclass(Dataset, BaseTableModel)

    def test_project_inherits_base(self):
        """Test Project inherits from BaseTableModel."""
        from app.models import BaseTableModel, Project

        assert issubclass(Project, BaseTableModel)

    def test_task_inherits_base(self):
        """Test Task inherits from BaseTableModel."""
        from app.models import BaseTableModel, Task

        assert issubclass(Task, BaseTableModel)

    def test_audit_log_does_not_inherit_base(self):
        """Test AuditLog does NOT inherit BaseTableModel (no soft delete)."""
        from sqlmodel import SQLModel

        from app.models import AuditLog

        # AuditLog should inherit directly from SQLModel, not BaseTableModel
        assert issubclass(AuditLog, SQLModel)
        # AuditLog should NOT have is_deleted property
        assert not hasattr(AuditLog, "is_deleted")


class TestModelTableArgs:
    """Test models have proper table constraints defined."""

    def test_user_has_email_index(self):
        """Test User model has index on email."""
        from app.models import User

        table_args = User.__table_args__
        index_names = [idx.name for idx in table_args if hasattr(idx, "name")]
        assert "idx_users_email" in index_names

    def test_dataset_has_slug_unique(self):
        """Test Dataset model has unique constraint on slug."""
        from app.models import Dataset

        table_args = Dataset.__table_args__
        constraint_names = [c.name for c in table_args if hasattr(c, "name")]
        assert "uq_datasets_slug" in constraint_names

    def test_task_has_project_entry_unique(self):
        """Test Task model has unique constraint on project_id + dataset_entry_id."""
        from app.models import Task

        table_args = Task.__table_args__
        constraint_names = [c.name for c in table_args if hasattr(c, "name")]
        assert "uq_tasks_project_entry" in constraint_names
