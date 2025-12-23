"""
Pydantic schemas for request/response validation.

Re-exports all schemas for convenient importing:
    from app.schemas import UserCreate, UserRead, TaskStatus
"""

from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
    TimestampMixin,
    UUIDMixin,
)
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
]
