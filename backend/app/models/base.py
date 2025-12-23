"""
Base SQLModel classes with common fields and mixins.

Design decisions:
- Use SQLModel for combined Pydantic + SQLAlchemy functionality
- Separate table models (with table=True) from schema models
- Use mixins for timestamp and soft-delete functionality
- BigInteger for IDs to support large datasets
- UUID for public-facing identifiers (never expose internal IDs)
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import BigInteger, Column, DateTime, Index, event, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, SQLModel

__all__ = [
    "SQLModel",
    "BaseTableModel",
    "TimestampMixin",
    "SoftDeleteMixin",
]


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps."""

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


class SoftDeleteMixin:
    """
    Mixin providing soft-delete functionality.

    Records are never truly deleted - deleted_at is set instead.
    All queries should filter by deleted_at IS NULL by default.
    """

    deleted_at: datetime | None = Field(
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


class BaseTableModel(TimestampMixin, SoftDeleteMixin, SQLModel):
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
    """

    # Class-level attributes for SQLModel/SQLAlchemy
    __table_args__: ClassVar[tuple[Any, ...]] = ()

    # Primary key - internal use only, never exposed
    id: int | None = Field(
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

    @declared_attr
    @classmethod
    def __table_args__(cls) -> tuple:
        """
        Override in subclasses to add indexes and constraints.

        Example:
            @declared_attr
            @classmethod
            def __table_args__(cls) -> tuple:
                return (
                    Index("idx_users_email", "email"),
                    UniqueConstraint("email", name="uq_users_email"),
                )
        """
        return ()


# SQLAlchemy event listener to auto-update updated_at
@event.listens_for(BaseTableModel, "before_update", propagate=True)
def receive_before_update(mapper: Any, connection: Any, target: BaseTableModel) -> None:
    """Auto-update updated_at timestamp on any model update."""
    target.updated_at = datetime.utcnow()
