"""
User model - system users who can own projects and review candidates.

Design notes:
- password_hash is nullable to support SSO-only users in the future
- settings JSONB allows flexible user preferences without schema changes
- status uses VARCHAR with enum validation in Pydantic (not DB enum)
- Relationships are defined without back_populates to avoid circular issues
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import BaseTableModel

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

    # Note: Relationships to projects and audit_logs are accessed via queries
    # Example: session.exec(select(Project).where(Project.owner_id == user.id))
