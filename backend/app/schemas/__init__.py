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
]
