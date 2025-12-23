"""
SQLModel/SQLAlchemy ORM models.

Re-exports all models for convenient importing:
    from app.models import User, Project, Task

Import order matters due to relationship dependencies.
"""

# Base must be imported first
from app.models.base import BaseTableModel, SQLModel

# Import in dependency order to avoid circular import issues
from app.models.user import User
from app.models.dataset import Dataset
from app.models.property_definition import PropertyDefinition
from app.models.dataset_entry import DatasetEntry
from app.models.dataset_entry_property import DatasetEntryProperty
from app.models.project import Project
from app.models.task import Task
from app.models.match_candidate import MatchCandidate
from app.models.audit_log import AuditLog

__all__ = [
    # Base
    "SQLModel",
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
