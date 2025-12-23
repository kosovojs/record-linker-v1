"""
Enum definitions for the Record Linker application.

All enums are defined as StrEnum for JSON serialization compatibility.
Database stores these as VARCHAR - validation happens at Pydantic/FastAPI layer.
"""

from enum import StrEnum

__all__ = [
    "UserRole",
    "UserStatus",
    "DatasetSourceType",
    "PropertyDataType",
    "PropertyValueSource",
    "ProjectStatus",
    "TaskStatus",
    "CandidateStatus",
    "CandidateSource",
]


class UserRole(StrEnum):
    """User permission levels."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class UserStatus(StrEnum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    PENDING_VERIFICATION = "pending_verification"


class DatasetSourceType(StrEnum):
    """How dataset data was obtained."""

    WEB_SCRAPE = "web_scrape"
    API = "api"
    FILE_IMPORT = "file_import"
    MANUAL = "manual"


class PropertyDataType(StrEnum):
    """
    Hint for UI rendering and validation.

    Note: All values are stored as TEXT in the EAV table.
    This is a hint for client-side handling.
    """

    TEXT = "text"
    DATE = "date"
    NUMBER = "number"
    URL = "url"
    EMAIL = "email"
    IDENTIFIER = "identifier"


class PropertyValueSource(StrEnum):
    """How a property value was obtained."""

    IMPORT = "import"
    MANUAL = "manual"
    DERIVED = "derived"
    API = "api"


class ProjectStatus(StrEnum):
    """
    Project lifecycle states.

    State machine:
    draft -> active -> pending_search -> search_in_progress -> search_completed
                    -> pending_processing -> processing -> review_ready -> completed
                                          -> processing_failed (retry -> processing)
    Any state -> archived
    """

    DRAFT = "draft"
    ACTIVE = "active"
    PENDING_SEARCH = "pending_search"
    SEARCH_IN_PROGRESS = "search_in_progress"
    SEARCH_COMPLETED = "search_completed"
    PENDING_PROCESSING = "pending_processing"
    PROCESSING = "processing"
    PROCESSING_FAILED = "processing_failed"
    REVIEW_READY = "review_ready"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    """
    Task processing states.

    State machine:
    new -> queued_for_processing -> processing -> awaiting_review -> reviewed
                                              -> no_candidates_found -> skipped
                                              -> failed (retry -> queued_for_processing)
                                              -> auto_confirmed
                                              -> knowledge_based
    """

    NEW = "new"
    QUEUED_FOR_PROCESSING = "queued_for_processing"
    PROCESSING = "processing"
    FAILED = "failed"
    NO_CANDIDATES_FOUND = "no_candidates_found"
    AWAITING_REVIEW = "awaiting_review"
    REVIEWED = "reviewed"
    AUTO_CONFIRMED = "auto_confirmed"
    SKIPPED = "skipped"
    KNOWLEDGE_BASED = "knowledge_based"


class CandidateStatus(StrEnum):
    """Match candidate decision states."""

    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CandidateSource(StrEnum):
    """How a candidate was discovered."""

    AUTOMATED_SEARCH = "automated_search"
    MANUAL = "manual"
    FILE_IMPORT = "file_import"
    AI_SUGGESTION = "ai_suggestion"
    KNOWLEDGE_BASE = "knowledge_base"
