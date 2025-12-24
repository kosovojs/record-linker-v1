"""
User model - system users who can own projects and review candidates.

Design notes:
- password_hash is nullable to support SSO-only users in the future
- settings uses UserSettings typed schema for structure validation
- status and role use enums for type safety
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from app.models.base import BaseTableModel
from app.schemas.enums import UserRole, UserStatus
from app.schemas.jsonb_types import UserSettings

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
    password_hash: str | None = Field(
        default=None,
        sa_column=Column(String(255), nullable=True),
    )

    # Status fields - using enums for type safety
    # Stored as VARCHAR in DB, validated as enum in Python
    role: UserRole = Field(
        default=UserRole.USER,
        sa_column=Column(String(50), nullable=False),
    )
    status: UserStatus = Field(
        default=UserStatus.ACTIVE,
        sa_column=Column(String(50), nullable=False),
    )

    # Tracking
    last_login_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
    )

    # JSONB settings - use UserSettings.model_dump() when setting
    settings: dict = Field(
        default_factory=lambda: UserSettings().model_dump(),
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Helper methods for typed access
    def get_settings(self) -> UserSettings:
        """Get settings as typed Pydantic model."""
        return UserSettings.model_validate(self.settings)

    def set_settings(self, settings: UserSettings) -> None:
        """Set settings from typed Pydantic model."""
        self.settings = settings.model_dump()
