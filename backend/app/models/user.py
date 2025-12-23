"""
User model - system users who can own projects and review candidates.

Design notes:
- password_hash is nullable to support SSO-only users in the future
- settings JSONB allows flexible user preferences without schema changes
- status uses VARCHAR with enum validation in Pydantic (not DB enum)
  for easier enum evolution without migrations
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

from app.models.base import BaseTableModel

# TYPE_CHECKING import to avoid circular imports at runtime
# These are only used for type hints, not actual code
if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.project import Project

__all__ = ["User"]


class User(BaseTableModel, table=True):
    """
    System user who can create projects, review tasks, and accept/reject candidates.

    Roles:
    - admin: Full system access, can manage other users
    - user: Can create and manage own projects
    - viewer: Read-only access to assigned projects
    """

    __tablename__ = "users"
    __table_args__ = (
        # Partial unique index - only enforce uniqueness for non-deleted records
        # This allows "deleting" a user and creating a new one with same email
        UniqueConstraint("email", name="uq_users_email"),
        Index("idx_users_email", "email"),
        Index("idx_users_status", "status"),
        Index("idx_users_role", "role"),
    )

    # Core fields
    email: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
        description="Login identifier, must be unique",
    )
    display_name: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
        description="Human-readable name for UI display",
    )
    password_hash: str | None = Field(
        default=None,
        sa_column=Column(String(255), nullable=True),
        description="Bcrypt hash. Null for SSO-only users.",
    )

    # Status fields - use VARCHAR, enum validation happens in Pydantic layer
    role: str = Field(
        default="user",
        sa_column=Column(String(50), nullable=False),
        description="Permission level: admin, user, viewer",
    )
    status: str = Field(
        default="active",
        sa_column=Column(String(50), nullable=False),
        description="Account status: active, inactive, blocked, pending_verification",
    )

    # Tracking
    last_login_at: datetime | None = Field(
        default=None,
        description="Last successful login timestamp for security auditing",
    )

    # Flexible settings storage - allows adding user preferences
    # without schema migrations (e.g., UI theme, notification prefs)
    # Type is Any because SQLModel handles JSONB serialization
    settings: Any = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships - lazy loaded by default to avoid N+1
    # Use selectinload() in queries when you need these
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner",
        lazy="noload",  # Never auto-load, must be explicit
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user",
        lazy="noload",
    )
