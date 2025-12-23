"""
Pydantic schemas for request/response validation.

Re-exports all schemas for convenient importing:
    from app.schemas import UserCreate, UserRead, TaskStatus
"""

# Common schemas
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
    TimestampMixin,
    UUIDMixin,
)

# Enums
from app.schemas.enums import (
    CandidateSource,
    CandidateStatus,
    DatasetSourceType,
    ProjectStatus,
    PropertyDataType,
    PropertyValueSource,
    TaskStatus,
    UserRole,
    UserStatus,
)

# JSONB types
from app.schemas.jsonb_types import (
    CandidateExtraData,
    CandidateMatchedProperties,
    CandidateScoreBreakdown,
    DatasetEntryExtraData,
    DatasetExtraData,
    MatchingWeights,
    ProjectConfig,
    PropertyMatch,
    SearchStrategy,
    TaskExtraData,
    TaskProcessingInfo,
    UserSettings,
)

# Entity schemas - User
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserRead,
    UserUpdate,
)

# Entity schemas - Dataset
from app.schemas.dataset import (
    DatasetBase,
    DatasetCreate,
    DatasetRead,
    DatasetUpdate,
)

# Entity schemas - PropertyDefinition
from app.schemas.property_definition import (
    PropertyDefinitionBase,
    PropertyDefinitionCreate,
    PropertyDefinitionRead,
    PropertyDefinitionUpdate,
)

# Entity schemas - DatasetEntry
from app.schemas.dataset_entry import (
    DatasetEntryBase,
    DatasetEntryCreate,
    DatasetEntryRead,
    DatasetEntryUpdate,
)

# Entity schemas - DatasetEntryProperty
from app.schemas.dataset_entry_property import (
    DatasetEntryPropertyBase,
    DatasetEntryPropertyCreate,
    DatasetEntryPropertyRead,
    DatasetEntryPropertyUpdate,
)

# Entity schemas - Project
from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)

# Entity schemas - Task
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)

# Entity schemas - MatchCandidate
from app.schemas.match_candidate import (
    MatchCandidateBase,
    MatchCandidateCreate,
    MatchCandidateRead,
    MatchCandidateUpdate,
)

# Entity schemas - AuditLog
from app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogRead,
)

__all__ = [
    # Common
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "PaginationParams",
    "TimestampMixin",
    "UUIDMixin",
    # Enums
    "CandidateSource",
    "CandidateStatus",
    "DatasetSourceType",
    "ProjectStatus",
    "PropertyDataType",
    "PropertyValueSource",
    "TaskStatus",
    "UserRole",
    "UserStatus",
    # JSONB Types
    "CandidateExtraData",
    "CandidateMatchedProperties",
    "CandidateScoreBreakdown",
    "DatasetEntryExtraData",
    "DatasetExtraData",
    "MatchingWeights",
    "ProjectConfig",
    "PropertyMatch",
    "SearchStrategy",
    "TaskExtraData",
    "TaskProcessingInfo",
    "UserSettings",
    # User
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    # Dataset
    "DatasetBase",
    "DatasetCreate",
    "DatasetRead",
    "DatasetUpdate",
    # PropertyDefinition
    "PropertyDefinitionBase",
    "PropertyDefinitionCreate",
    "PropertyDefinitionRead",
    "PropertyDefinitionUpdate",
    # DatasetEntry
    "DatasetEntryBase",
    "DatasetEntryCreate",
    "DatasetEntryRead",
    "DatasetEntryUpdate",
    # DatasetEntryProperty
    "DatasetEntryPropertyBase",
    "DatasetEntryPropertyCreate",
    "DatasetEntryPropertyRead",
    "DatasetEntryPropertyUpdate",
    # Project
    "ProjectBase",
    "ProjectCreate",
    "ProjectRead",
    "ProjectUpdate",
    # Task
    "TaskBase",
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
    # MatchCandidate
    "MatchCandidateBase",
    "MatchCandidateCreate",
    "MatchCandidateRead",
    "MatchCandidateUpdate",
    # AuditLog
    "AuditLogCreate",
    "AuditLogRead",
]
