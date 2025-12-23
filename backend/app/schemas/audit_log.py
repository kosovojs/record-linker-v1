"""
AuditLog request/response schemas for API endpoints.

Patterns:
- AuditLogCreate: POST request body (for system/service layer use)
- AuditLogRead: Response body - audit logs are immutable, no Update schema

Note: Audit logs are typically created by the service layer, not directly
via API endpoints. The Create schema is provided for internal use.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AuditLogCreate",
    "AuditLogRead",
]


class AuditLogCreate(BaseModel):
    """Schema for creating a new audit log entry (internal use)."""

    user_uuid: UUID | None = Field(
        default=None,
        description="UUID of the user who performed the action (null for system actions)",
    )
    action: str = Field(
        min_length=1,
        max_length=100,
        description="Action type (e.g., 'project.created', 'task.reviewed')",
    )
    entity_type: str = Field(
        min_length=1,
        max_length=50,
        description="Type of entity affected (e.g., 'project', 'task')",
    )
    entity_uuid: UUID | None = Field(
        default=None,
        description="Public UUID of affected entity",
    )
    old_value: dict[str, Any] | None = Field(
        default=None,
        description="Previous state (for updates)",
    )
    new_value: dict[str, Any] | None = Field(
        default=None,
        description="New state (for updates)",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Request context (IP, user agent, etc.)",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description of the action",
    )


class AuditLogRead(BaseModel):
    """Schema for audit log API responses. Audit logs are immutable."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    user_uuid: UUID | None = Field(
        default=None,
        description="User UUID (populated by service layer)",
    )
    action: str = Field(description="Action type")
    entity_type: str = Field(description="Entity type")
    entity_uuid: UUID | None = Field(description="Entity UUID")
    old_value: dict[str, Any] | None = Field(description="Previous state")
    new_value: dict[str, Any] | None = Field(description="New state")
    context: dict[str, Any] = Field(description="Request context")
    description: str | None = Field(description="Action description")
    created_at: datetime = Field(description="When action occurred")
