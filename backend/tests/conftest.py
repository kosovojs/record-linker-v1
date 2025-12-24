"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import Settings
from app.database import get_db
from app.main import app

# Test database URL (using SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# ============================================================================
# JSONB → JSON compatibility for SQLite
# SQLite doesn't have JSONB, so we need to render it as JSON (which is TEXT)
# ============================================================================
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler


# Patch SQLite's type compiler to handle JSONB
def _visit_JSONB(self, type_, **kw):
    return "JSON"


SQLiteTypeCompiler.visit_JSONB = _visit_JSONB


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings with test database."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key",
        debug=True,
    )


@pytest.fixture(scope="session")
async def test_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Import all models explicitly to ensure they're registered with SQLModel.metadata
    # This is necessary for proper FK ordering during table creation
    from app.models.audit_log import AuditLog  # noqa: F401
    from app.models.dataset import Dataset  # noqa: F401
    from app.models.dataset_entry import DatasetEntry  # noqa: F401
    from app.models.dataset_entry_property import DatasetEntryProperty  # noqa: F401
    from app.models.match_candidate import MatchCandidate  # noqa: F401
    from app.models.project import Project  # noqa: F401
    from app.models.property_definition import PropertyDefinition  # noqa: F401
    from app.models.task import Task  # noqa: F401
    from app.models.user import User  # noqa: F401

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for each test with proper cleanup."""
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        yield session

        # Clean up all tables after each test to ensure isolation
        # Order matters due to foreign key constraints (delete children first)
        from app.models.audit_log import AuditLog
        from app.models.dataset import Dataset
        from app.models.dataset_entry import DatasetEntry
        from app.models.dataset_entry_property import DatasetEntryProperty
        from app.models.match_candidate import MatchCandidate
        from app.models.project import Project
        from app.models.property_definition import PropertyDefinition
        from app.models.task import Task
        from app.models.user import User

        # Delete in order respecting FKs
        for model in [
            AuditLog,
            MatchCandidate,
            Task,
            Project,
            DatasetEntryProperty,
            DatasetEntry,
            PropertyDefinition,
            Dataset,
            User,
        ]:
            await session.execute(model.__table__.delete())
        await session.commit()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
