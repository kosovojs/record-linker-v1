"""
AuditLog model - tracks all significant actions for compliance.

Design notes:
- NO soft delete - audit logs are permanent records
- entity_uuid stored separately for querying even after entity deletion
- old_value/new_value capture state changes for debugging
- context stores request metadata (IP, user agent) for security audits
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from app.models.user import User

__all__ = ["AuditLog"]


class AuditLog(SQLModel, table=True):
    """
    Permanent record of significant actions in the system.

    Used for:
    - Security auditing (who did what, when)
    - Debugging (what changed and why)
    - Compliance (GDPR audit trails)

    Unlike other models, audit logs are NEVER deleted or soft-deleted.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_entity_uuid", "entity_type", "entity_uuid"),
        Index("idx_audit_created", "created_at"),
    )

    # Primary key - no soft delete for audit logs
    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), unique=True, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    # Who performed the action - null for system actions
    user_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )

    # What action was performed
    # Format: "entity.action" (e.g., "project.created", "candidate.accepted")
    action: str = Field(
        sa_column=Column(String(100), nullable=False),
        max_length=100,
    )

    # What entity was affected
    entity_type: str = Field(
        sa_column=Column(String(50), nullable=False),
        max_length=50,
        description="Type: project, task, candidate, user, etc.",
    )
    entity_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
        description="Internal ID of affected entity",
    )
    entity_uuid: uuid_lib.UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=True),
        description="Public UUID of affected entity (survives entity deletion)",
    )

    # State changes - what was the state before and after?
    old_value: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Previous state (for updates)",
    )
    new_value: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="New state (for updates)",
    )

    # Request context for security auditing
    # IP, user agent, request ID, batch ID for bulk ops
    context: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Human-readable description
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="audit_logs")
