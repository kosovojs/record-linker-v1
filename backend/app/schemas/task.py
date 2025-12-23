"""
Task request/response schemas for API endpoints.

Patterns:
- TaskBase: Shared validation for create/update
- TaskCreate: POST request body
- TaskUpdate: PATCH request body (all optional)
- TaskRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import TaskStatus

__all__ = [
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskRead",
]


class TaskBase(BaseModel):
    """Shared fields for task create/update operations."""

    notes: str | None = Field(
        default=None,
        description="Reviewer notes",
    )


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    project_uuid: UUID = Field(
        description="UUID of the parent project",
    )
    dataset_entry_uuid: UUID = Field(
        description="UUID of the dataset entry to match",
    )


class TaskUpdate(BaseModel):
    """Schema for updating a task. All fields optional."""

    status: TaskStatus | None = Field(
        default=None,
        description="Task status",
    )
    notes: str | None = Field(
        default=None,
        description="Reviewer notes",
    )
    accepted_wikidata_id: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^Q\d+$",
        description="Accepted Wikidata QID (e.g., 'Q12345')",
    )


class TaskRead(BaseModel):
    """Schema for task API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    project_uuid: UUID | None = Field(
        default=None,
        description="Parent project UUID (populated by service layer)",
    )
    dataset_entry_uuid: UUID | None = Field(
        default=None,
        description="Dataset entry UUID (populated by service layer)",
    )
    status: TaskStatus = Field(description="Task status")
    accepted_wikidata_id: str | None = Field(description="Accepted Wikidata QID")
    candidate_count: int = Field(description="Number of candidates found")
    highest_score: int | None = Field(description="Highest candidate score")
    processing_started_at: datetime | None = Field(description="Processing start time")
    processing_completed_at: datetime | None = Field(description="Processing end time")
    reviewed_at: datetime | None = Field(description="Review timestamp")
    reviewed_by_uuid: UUID | None = Field(
        default=None,
        description="Reviewer UUID (populated by service layer)",
    )
    notes: str | None = Field(description="Reviewer notes")
    error_message: str | None = Field(description="Error details if failed")
    extra_data: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(description="When created")
    updated_at: datetime = Field(description="Last update timestamp")
