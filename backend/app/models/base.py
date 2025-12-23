"""
Base SQLModel classes with common fields.

Design decisions:
- Use SQLModel for combined Pydantic + SQLAlchemy functionality
- Separate table models (with table=True) from schema models
- BigInteger for IDs to support large datasets
- UUID for public-facing identifiers (never expose internal IDs)

Note on SQLModel: Don't use generic types like dict[str, Any] or list[str]
for fields - SQLModel's type resolution has issues with these. Use Any type
and let the sa_column definition handle the actual column type.
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

__all__ = [
    "SQLModel",
    "BaseTableModel",
]


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
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )

    # Public identifier - used in all API responses
    uuid: uuid_lib.UUID = Field(
        default_factory=uuid_lib.uuid4,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            unique=True,
            nullable=False,
            index=True,
        ),
    )

    # Timestamps - created_at and updated_at
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )

    # Soft delete - null means active, set means deleted
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
