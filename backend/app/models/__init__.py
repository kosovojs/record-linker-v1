"""
SQLModel/SQLAlchemy ORM models.

Models are imported lazily to avoid circular import issues.
Import specific models directly:
    from app.models.user import User
    from app.models.project import Project

Or import all at once (after all modules are loaded):
    from app.models import User, Project, Task
"""

# Re-export SQLModel for convenience
from sqlmodel import SQLModel

# Lazy imports - these are only resolved when accessed
# This avoids import-time type resolution issues in SQLModel

__all__ = [
    "SQLModel",
    # Base
    "BaseTableModel",
    # Models
    "User",
    "Dataset",
    "PropertyDefinition",
    "DatasetEntry",
    "DatasetEntryProperty",
    "Project",
    "Task",
    "MatchCandidate",
    "AuditLog",
]


def __getattr__(name: str):
    """
    Lazy import of models to avoid circular import issues.

    This is called when an attribute is accessed that doesn't exist
    in the module namespace. We use it to defer model imports until
    they're actually needed.
    """
    if name == "BaseTableModel":
        from app.models.base import BaseTableModel
        return BaseTableModel
    elif name == "User":
        from app.models.user import User
        return User
    elif name == "Dataset":
        from app.models.dataset import Dataset
        return Dataset
    elif name == "PropertyDefinition":
        from app.models.property_definition import PropertyDefinition
        return PropertyDefinition
    elif name == "DatasetEntry":
        from app.models.dataset_entry import DatasetEntry
        return DatasetEntry
    elif name == "DatasetEntryProperty":
        from app.models.dataset_entry_property import DatasetEntryProperty
        return DatasetEntryProperty
    elif name == "Project":
        from app.models.project import Project
        return Project
    elif name == "Task":
        from app.models.task import Task
        return Task
    elif name == "MatchCandidate":
        from app.models.match_candidate import MatchCandidate
        return MatchCandidate
    elif name == "AuditLog":
        from app.models.audit_log import AuditLog
        return AuditLog

    raise AttributeError(f"module 'app.models' has no attribute '{name}'")
