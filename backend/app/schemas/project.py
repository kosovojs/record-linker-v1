"""
Project request/response schemas for API endpoints.

Patterns:
- ProjectBase: Shared validation for create/update
- ProjectCreate: POST request body
- ProjectUpdate: PATCH request body (all optional)
- ProjectRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import ProjectStatus
from app.schemas.jsonb_types import ProjectConfig

__all__ = [
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectRead",
]


class ProjectBase(BaseModel):
    """Shared fields for project create/update operations."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Project name",
    )
    description: str | None = Field(
        default=None,
        description="Project description and notes",
    )


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    dataset_uuid: UUID = Field(
        description="UUID of the dataset being reconciled",
    )
    owner_uuid: UUID | None = Field(
        default=None,
        description="UUID of the project owner (defaults to current user)",
    )
    config: ProjectConfig | None = Field(
        default=None,
        description="Project configuration (uses defaults if not provided)",
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a project. All fields optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Project name",
    )
    description: str | None = Field(
        default=None,
        description="Project description",
    )
    status: ProjectStatus | None = Field(
        default=None,
        description="Project status",
    )
    config: ProjectConfig | None = Field(
        default=None,
        description="Project configuration",
    )


class ProjectRead(BaseModel):
    """Schema for project API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    dataset_uuid: UUID | None = Field(
        default=None,
        description="Dataset UUID (populated by service layer)",
    )
    owner_uuid: UUID | None = Field(
        default=None,
        description="Owner UUID (populated by service layer)",
    )
    name: str = Field(description="Project name")
    description: str | None = Field(description="Project description")
    status: ProjectStatus = Field(description="Project status")
    task_count: int = Field(description="Total number of tasks")
    tasks_completed: int = Field(description="Completed tasks count")
    tasks_with_candidates: int = Field(description="Tasks with candidates count")
    config: dict = Field(default_factory=dict, description="Project configuration")
    started_at: datetime | None = Field(description="When processing started")
    completed_at: datetime | None = Field(description="When project completed")
    created_at: datetime = Field(description="When created")
    updated_at: datetime = Field(description="Last update timestamp")

    @field_validator("config", mode="before")
    @classmethod
    def parse_config(cls, v):
        """Parse config from JSON string if needed (SQLite compatibility)."""
        import json
        if v is None:
            return {}
        if isinstance(v, str):
            return json.loads(v)
        return v
