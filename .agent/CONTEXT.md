# Record Linker - Agent Context

> **Purpose**: This file preserves the context of the development conversation so work can be resumed in a fresh session.
> **Last Updated**: 2023-12-23

## Project Overview

**Record Linker** is a web application for linking external dataset records (e.g., EliteProspects players, IMDB actors) to Wikidata entities. It provides a workflow for:
1. Importing dataset entries
2. Auto-generating match candidates via Wikidata searches
3. Human review and acceptance/rejection of matches
4. Exporting confirmed matches

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + SQLModel + asyncpg |
| Database | PostgreSQL (with JSONB) |
| Async ORM | SQLModel (Pydantic + SQLAlchemy) |
| Frontend | TBD (likely Vue.js or React) |

## Key Documentation

- [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) - Full project requirements and Q&A
- [docs/MODEL_SCHEMA.md](docs/MODEL_SCHEMA.md) - Database schema design with field specifications

## Implementation Progress

### ✅ Completed Phases

#### Phase 1: Project Setup
- FastAPI application structure
- Health check endpoints (`/health`, `/`)
- Async database configuration
- Test infrastructure with pytest-asyncio

#### Phase 2: Enums & Base Models
- **Enums** (`app/schemas/enums.py`): UserRole, UserStatus, DatasetSourceType, ProjectStatus, TaskStatus, CandidateStatus, CandidateSource, PropertyDataType, PropertyValueSource
- **Common Schemas** (`app/schemas/common.py`): PaginationParams, PaginatedResponse, ErrorResponse
- **Base Model** (`app/models/base.py`): BaseTableModel with id, uuid, timestamps, soft delete

#### Phase 3: ORM Models (Current)
All 9 models implemented in `app/models/`:

| Model | File | Key Features |
|-------|------|--------------|
| User | `user.py` | UserRole/UserStatus enums, UserSettings JSONB |
| Dataset | `dataset.py` | DatasetSourceType enum, DatasetExtraData JSONB |
| PropertyDefinition | `property_definition.py` | EAV pattern attributes |
| DatasetEntry | `dataset_entry.py` | External ID linking, raw_data storage |
| DatasetEntryProperty | `dataset_entry_property.py` | EAV values with normalization |
| Project | `project.py` | ProjectStatus enum, ProjectConfig JSONB |
| Task | `task.py` | TaskStatus enum, TaskExtraData JSONB |
| MatchCandidate | `match_candidate.py` | CandidateStatus/Source enums, score breakdowns |
| AuditLog | `audit_log.py` | Permanent records (no soft delete) |

### Typed JSONB Schemas (`app/schemas/jsonb_types.py`)

All JSONB columns have corresponding Pydantic models for type safety:

```
UserSettings          -> users.settings
DatasetExtraData      -> datasets.extra_data
DatasetEntryExtraData -> dataset_entries.extra_data
ProjectConfig         -> projects.config (matching weights, thresholds)
TaskExtraData         -> tasks.extra_data (processing info)
CandidateScoreBreakdown    -> match_candidates.score_breakdown
CandidateMatchedProperties -> match_candidates.matched_properties
CandidateExtraData         -> match_candidates.extra_data
```

Each model has `get_*()` and `set_*()` helper methods for typed access.

### 📋 Remaining Phases

#### Phase 4: Request/Response Schemas
- Create/Update/Read Pydantic schemas for each entity
- API response models with UUID exposure (never internal IDs)

#### Phase 5: API Endpoints
- CRUD endpoints for all entities
- Bulk operations (import entries, update candidates)
- Search/filter endpoints

#### Phase 6: Services Layer
- Business logic separation
- Wikidata integration service
- Matching/scoring algorithms

#### Phase 7: Migrations
- Alembic setup
- Initial migration generation

## Key Design Decisions

### 1. No SQLModel Relationship()
SQLModel's `Relationship()` has issues with forward references when using `from __future__ import annotations`. Relationships are accessed via explicit queries in the service layer instead - this actually prevents N+1 issues by forcing explicit eager loading.

### 2. Enums as VARCHAR
Enums are stored as VARCHAR in the database (not PostgreSQL ENUM type) to allow adding new values without migrations. Validation happens at the Pydantic layer using `StrEnum`.

### 3. JSONB with Typed Schemas
JSONB columns use Pydantic models for structure validation. Each has a `schema_version` field for future migrations.

### 4. Soft Delete Pattern
All models (except AuditLog) inherit `deleted_at` for soft deletion. Use `model.soft_delete()` and `model.restore()` methods.

### 5. UUID for Public IDs
Internal `id` (BIGINT) is never exposed. Public API uses `uuid` field. Foreign keys use internal IDs for performance.

## Test Coverage

**68 tests passing** covering:
- Health endpoints
- Enum values and serialization
- Common schemas (pagination, errors)
- JSONB typed schemas
- Model imports and inheritance
- Base model features (soft delete, UUID, defaults)

Run tests: `cd backend && .venv\Scripts\pytest -v`

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py           # Settings via pydantic-settings
│   ├── database.py         # Async engine setup
│   ├── main.py             # FastAPI app entry point
│   ├── api/
│   │   ├── deps.py         # FastAPI dependencies
│   │   └── v1/             # API version 1 routes (TBD)
│   ├── models/
│   │   ├── __init__.py     # Lazy imports to avoid circular refs
│   │   ├── base.py         # BaseTableModel
│   │   ├── user.py
│   │   ├── dataset.py
│   │   ├── property_definition.py
│   │   ├── dataset_entry.py
│   │   ├── dataset_entry_property.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── match_candidate.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── __init__.py     # Re-exports all schemas
│   │   ├── common.py       # Pagination, errors
│   │   ├── enums.py        # All StrEnum definitions
│   │   └── jsonb_types.py  # Typed JSONB schemas
│   ├── services/           # Business logic (TBD)
│   └── utils/
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api/
│   ├── test_models/
│   └── test_schemas/
├── pyproject.toml
└── README.md
```

## Next Steps (for new session)

1. **Run tests** to verify state: `cd backend && .venv\Scripts\pytest -v`
2. **Continue with Phase 4**: Create request/response Pydantic schemas
3. **Reference**: Check `docs/MODEL_SCHEMA.md` for field specifications

## Common Commands

```powershell
# Activate environment
cd backend
.venv\Scripts\activate

# Run tests
.venv\Scripts\pytest -v

# Run single test file
.venv\Scripts\pytest tests/test_models/test_base.py -v

# Start dev server (once API is ready)
.venv\Scripts\uvicorn app.main:app --reload
```
