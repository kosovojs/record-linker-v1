"""
Base SQLModel classes with common fields.

Design decisions:
- Use SQLModel for combined Pydantic + SQLAlchemy functionality
- BigInteger for IDs to support large datasets
- UUID for public-facing identifiers (never expose internal IDs)

Note on Column reuse: SQLAlchemy Column objects cannot be shared between
tables. When using inheritance, we must define columns without sa_column
or use sa_column_kwargs to avoid sharing Column objects.
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

__all__ = [
    "SQLModel",
    "BaseTableModel",
]


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


class BaseTableModel(SQLModel):
    """
    Base class for all database table models.

    Provides:
    - id: Internal BigInteger primary key (never exposed via API)
    - uuid: Public UUID identifier (used in all API responses)
    - created_at, updated_at: Automatic timestamps
    - deleted_at: Soft-delete support

    Usage:
        class User(BaseTableModel, table=True):
            __tablename__ = "users"
            email: str = Field(max_length=255)

    Note: Subclasses must set table=True to create actual tables.
    """

    # Primary key - internal use only, never exposed
    # Using sa_column_kwargs instead of sa_column to avoid Column reuse
    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    # Public identifier - used in all API responses
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        unique=True,
        index=True,
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=sa.DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=sa.DateTime(timezone=True),
    )

    # Soft delete - null means active, set means deleted
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
