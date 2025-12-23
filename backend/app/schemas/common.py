"""
Common Pydantic schemas shared across the application.

Provides:
- Pagination schemas (request params and response wrapper)
- UUID mixin for consistent public ID handling
- Error response schemas
- Health check schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "PaginationParams",
    "PaginatedResponse",
    "UUIDMixin",
    "TimestampMixin",
    "ErrorResponse",
    "ErrorDetail",
    "HealthResponse",
]

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page (max 100)",
    )

    @property
    def offset(self) -> int:
        """Calculate SQL OFFSET from page number."""
        return (self.page - 1) * self.page_size


class PaginatedResponse[T](BaseModel):
    """
    Generic paginated response wrapper.

    Usage:
        @app.get("/users", response_model=PaginatedResponse[UserRead])
        async def list_users(...):
            return PaginatedResponse(
                items=users,
                total=total_count,
                page=pagination.page,
                page_size=pagination.page_size,
            )
    """

    items: list[T]
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")

    @property
    def pages(self) -> int:
        """Calculate total number of pages."""
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    model_config = ConfigDict(
        # Include computed fields in JSON serialization
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
            }
        }
    )


class UUIDMixin(BaseModel):
    """Mixin providing UUID field for response schemas."""

    uuid: UUID = Field(description="Unique public identifier")


class TimestampMixin(BaseModel):
    """Mixin providing timestamp fields for response schemas."""

    created_at: datetime = Field(description="When the record was created")
    updated_at: datetime = Field(description="When the record was last updated")


class ErrorDetail(BaseModel):
    """Detailed error information."""

    loc: list[str] = Field(description="Error location path")
    msg: str = Field(description="Error message")
    type: str = Field(description="Error type")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str | list[ErrorDetail] = Field(description="Error details")

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Resource not found"}})


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Health status")
    app: str = Field(description="Application name")
    version: str | None = Field(default=None, description="Application version")
