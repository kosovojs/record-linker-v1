"""Tests for User request/response schemas."""

from uuid import uuid4
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.user import UserBase, UserCreate, UserUpdate, UserRead
from app.schemas.enums import UserRole, UserStatus
from app.schemas.jsonb_types import UserSettings


class TestUserBase:
    """Tests for UserBase schema."""

    def test_valid_user_base(self):
        """Test creating valid UserBase."""
        user = UserBase(
            email="test@example.com",
            display_name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

    def test_invalid_email_format(self):
        """Test that invalid email format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="invalid-email", display_name="Test")
        assert "email" in str(exc_info.value)

    def test_empty_display_name_rejected(self):
        """Test that empty display name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="test@example.com", display_name="")
        assert "display_name" in str(exc_info.value)

    def test_email_max_length(self):
        """Test email max length validation."""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError):
            UserBase(email=long_email, display_name="Test")


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_valid_user_create_minimal(self):
        """Test creating user with minimal required fields."""
        user = UserCreate(
            email="test@example.com",
            display_name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER  # Default
        assert user.password is None
        assert user.settings is None

    def test_valid_user_create_full(self):
        """Test creating user with all fields."""
        settings = UserSettings()
        user = UserCreate(
            email="admin@example.com",
            display_name="Admin User",
            password="SecurePassword123!",
            role=UserRole.ADMIN,
            settings=settings,
        )
        assert user.role == UserRole.ADMIN
        assert user.password == "SecurePassword123!"
        assert user.settings is not None

    def test_password_min_length(self):
        """Test password minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                display_name="Test",
                password="short",
            )
        assert "password" in str(exc_info.value)

    def test_invalid_role_rejected(self):
        """Test that invalid role value is rejected."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                display_name="Test",
                role="superadmin",  # Invalid role
            )


class TestUserUpdate:
    """Tests for UserUpdate schema."""

    def test_empty_update_allowed(self):
        """Test that empty update is valid (all fields optional)."""
        update = UserUpdate()
        assert update.email is None
        assert update.display_name is None
        assert update.role is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        update = UserUpdate(
            display_name="New Name",
            status=UserStatus.INACTIVE,
        )
        assert update.display_name == "New Name"
        assert update.status == UserStatus.INACTIVE
        assert update.email is None

    def test_all_fields_update(self):
        """Test update with all fields."""
        update = UserUpdate(
            email="new@example.com",
            display_name="New Name",
            password="NewPassword123!",
            role=UserRole.VIEWER,
            status=UserStatus.BLOCKED,
            settings=UserSettings(),
        )
        assert update.email == "new@example.com"
        assert update.role == UserRole.VIEWER
        assert update.status == UserStatus.BLOCKED


class TestUserRead:
    """Tests for UserRead schema."""

    def test_valid_user_read(self):
        """Test creating UserRead from valid data."""
        now = datetime.utcnow()
        user = UserRead(
            uuid=uuid4(),
            email="test@example.com",
            display_name="Test User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            last_login_at=now,
            settings={},
            created_at=now,
            updated_at=now,
        )
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER

    def test_user_read_from_dict(self):
        """Test creating UserRead from dict (like DB result)."""
        now = datetime.utcnow()
        data = {
            "uuid": uuid4(),
            "email": "test@example.com",
            "display_name": "Test",
            "role": "user",
            "status": "active",
            "last_login_at": None,
            "settings": {},
            "created_at": now,
            "updated_at": now,
        }
        user = UserRead.model_validate(data)
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE

    def test_user_read_missing_required_field(self):
        """Test that missing required field raises error."""
        with pytest.raises(ValidationError):
            UserRead(
                uuid=uuid4(),
                # Missing email and other required fields
            )
