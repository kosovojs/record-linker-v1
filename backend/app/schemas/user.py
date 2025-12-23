"""
User request/response schemas for API endpoints.

Patterns:
- UserBase: Shared validation for create/update
- UserCreate: POST request body
- UserUpdate: PATCH request body (all optional)
- UserRead: Response body with UUID and timestamps
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.enums import UserRole, UserStatus
from app.schemas.jsonb_types import UserSettings

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
]


class UserBase(BaseModel):
    """Shared fields for user create/update operations."""

    email: EmailStr = Field(
        max_length=255,
        description="User's email address (login identifier)",
    )
    display_name: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable display name",
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Password (null for SSO-only users)",
    )
    role: UserRole = Field(
        default=UserRole.USER,
        description="User permission level",
    )
    settings: UserSettings | None = Field(
        default=None,
        description="User preferences (uses defaults if not provided)",
    )


class UserUpdate(BaseModel):
    """Schema for updating an existing user. All fields optional."""

    email: EmailStr | None = Field(
        default=None,
        max_length=255,
        description="User's email address",
    )
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Display name",
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="New password",
    )
    role: UserRole | None = Field(
        default=None,
        description="User permission level",
    )
    status: UserStatus | None = Field(
        default=None,
        description="Account status",
    )
    settings: UserSettings | None = Field(
        default=None,
        description="User preferences",
    )


class UserRead(BaseModel):
    """Schema for user API responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Unique public identifier")
    email: str = Field(description="User's email address")
    display_name: str = Field(description="Display name")
    role: UserRole = Field(description="User permission level")
    status: UserStatus = Field(description="Account status")
    last_login_at: datetime | None = Field(description="Last login timestamp")
    settings: dict = Field(description="User preferences")
    created_at: datetime = Field(description="When user was created")
    updated_at: datetime = Field(description="Last update timestamp")
