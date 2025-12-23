"""
User model - system users who can own projects and review candidates.

Design notes:
- password_hash is nullable to support SSO-only users in the future
- settings JSONB allows flexible user preferences without schema changes
- status uses VARCHAR with enum validation in Pydantic (not DB enum)
  for easier enum evolution without migrations
- Relationships use SQLModel's Relationship() not SQLAlchemy's relationship()
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import BaseTableModel

# TYPE_CHECKING import to avoid circular imports at runtime
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
        UniqueConstraint("email", name="uq_users_email"),
        Index("idx_users_email", "email"),
        Index("idx_users_status", "status"),
        Index("idx_users_role", "role"),
    )

    # Core fields
    email: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
    )
    display_name: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
    )
    password_hash: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), nullable=True),
    )

    # Status fields
    role: str = Field(
        default="user",
        sa_column=Column(String(50), nullable=False),
    )
    status: str = Field(
        default="active",
        sa_column=Column(String(50), nullable=False),
    )

    # Tracking
    last_login_at: Optional[datetime] = Field(default=None)

    # JSONB settings - using dict default, actual type is JSONB
    settings: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Relationships using SQLModel's Relationship()
    # back_populates links to the other side of the relationship
    projects: List["Project"] = Relationship(back_populates="owner")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")
