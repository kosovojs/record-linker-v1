"""Tests for common schemas."""

from uuid import uuid4

import pytest

from app.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
)


class TestPaginationParams:
    """Test pagination parameter handling."""

    def test_default_values(self):
        """Test default pagination values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_offset_calculation(self):
        """Test offset calculation from page number."""
        assert PaginationParams(page=1, page_size=20).offset == 0
        assert PaginationParams(page=2, page_size=20).offset == 20
        assert PaginationParams(page=3, page_size=10).offset == 20

    def test_custom_values(self):
        """Test custom pagination values."""
        params = PaginationParams(page=5, page_size=50)
        assert params.page == 5
        assert params.page_size == 50
        assert params.offset == 200


class TestPaginatedResponse:
    """Test paginated response wrapper."""

    def test_pages_calculation(self):
        """Test total pages calculation."""
        response = PaginatedResponse[str](
            items=["a", "b"],
            total=100,
            page=1,
            page_size=20,
        )
        assert response.pages == 5

    def test_pages_with_remainder(self):
        """Test pages calculation with non-even division."""
        response = PaginatedResponse[str](
            items=["a"],
            total=21,
            page=1,
            page_size=20,
        )
        assert response.pages == 2

    def test_empty_response(self):
        """Test empty response returns 0 pages."""
        response = PaginatedResponse[str](
            items=[],
            total=0,
            page=1,
            page_size=20,
        )
        assert response.pages == 0

    def test_has_next_prev(self):
        """Test has_next and has_prev properties."""
        # First page of multi-page result
        response = PaginatedResponse[str](
            items=["a"], total=50, page=1, page_size=20
        )
        assert response.has_next is True
        assert response.has_prev is False

        # Middle page
        response2 = PaginatedResponse[str](
            items=["a"], total=50, page=2, page_size=20
        )
        assert response2.has_next is True
        assert response2.has_prev is True

        # Last page
        response3 = PaginatedResponse[str](
            items=["a"], total=50, page=3, page_size=20
        )
        assert response3.has_next is False
        assert response3.has_prev is True


class TestErrorResponse:
    """Test error response schema."""

    def test_string_detail(self):
        """Test error with string detail."""
        error = ErrorResponse(detail="Not found")
        assert error.detail == "Not found"

    def test_list_detail(self):
        """Test error with list of details."""
        from app.schemas.common import ErrorDetail

        details = [
            ErrorDetail(loc=["body", "email"], msg="Invalid email", type="value_error"),
        ]
        error = ErrorResponse(detail=details)
        assert len(error.detail) == 1
