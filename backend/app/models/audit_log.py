"""
AuditLog model - tracks all significant actions for compliance.

Design notes:
- NO soft delete - audit logs are permanent records
- entity_uuid stored for querying even after entity deletion
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

__all__ = ["AuditLog"]


class AuditLog(SQLModel, table=True):
    """
    Permanent record of significant actions in the system.

    Unlike other models, audit logs are NEVER deleted.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_entity_uuid", "entity_type", "entity_uuid"),
        Index("idx_audit_created", "created_at"),
    )

    # Primary key - no soft delete
    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), unique=True, nullable=False),
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    # Who performed the action
    user_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True),
    )

    # What action was performed
    action: str = Field(
        sa_column=Column(String(100), nullable=False),
        max_length=100,
    )

    # What entity was affected
    entity_type: str = Field(
        sa_column=Column(String(50), nullable=False),
        max_length=50,
    )
    entity_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True),
    )
    entity_uuid: uuid_lib.UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=True),
    )

    # State changes
    old_value: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    new_value: dict | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Request context
    context: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Description
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Note: Relationship to user is accessed via queries
