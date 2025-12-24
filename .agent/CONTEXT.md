# Record Linker - Agent Context

> **Purpose**: This file preserves the context of the development conversation so work can be resumed in a fresh session.
> **Last Updated**: 2025-12-23

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
| Test DB | SQLite (with JSONB compatibility patches) |
| Frontend | TBD (likely Vue.js or React) |

## Key Documentation

- [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) - Full project requirements and Q&A
- [docs/MODEL_SCHEMA.md](docs/MODEL_SCHEMA.md) - Database schema design with field specifications
- [docs/API_SPECIFICATION_v2.md](docs/API_SPECIFICATION_v2.md) - Complete API endpoint specifications

## Implementation Progress

### ✅ Completed Phases

#### Phase 1-4: Foundation
- FastAPI application structure + health endpoints
- 9 ORM models with JSONB typed schemas
- 9 entity request/response Pydantic schemas
- Enums as VARCHAR with StrEnum validation

#### Phase 5: API Endpoints (In Progress)

**✅ COMPLETED (36 tests passing):**

| Router | Endpoints | Tests | Notes |
|--------|-----------|-------|-------|
| Datasets | 5 | 7 | CRUD with slug uniqueness |
| Properties | 5 | 7 | CRUD with name uniqueness |
| Projects | 5 | 7 | CRUD with dataset FK, N+1 fixed |
| Entries | 5 | 6 | Bulk create, nested under datasets |
| Tasks | 8 | 7 | Nested under projects + skip + alias |
| **Total** | **28** | **34+2** | Base tests: 36 passing |

**🔜 REMAINING:**

| Router | Endpoints | Notes |
|--------|-----------|-------|
| Candidates | 9 | CRUD + accept/reject/bulk |
| Project Workflow | 4 | start, rerun, stats, export |
| Audit Logs | 2 | Read-only |
| Wikidata | 1 | Search stub |

### 📋 Remaining Phases

#### Phase 5: API Endpoints ✅ Complete
- All CRUD endpoints implemented
- Bulk operations (import entries, update candidates)
- Search/filter endpoints
- Project workflow (start, rerun, stats, approved-matches)
- Audit logs (read-only)
- Wikidata search (stub)

#### Phase 6: Services Layer
- Business logic separation
- Wikidata integration service
- Matching/scoring algorithms

#### Phase 7: Migrations
- Alembic setup
- Initial migration generation

### Services Layer

All services in `app/services/` with common patterns:

| Service | Status | Key Features |
|---------|--------|--------------|
| `base.py` | ✅ | Generic CRUD, get_by_uuid, soft_delete |
| `exceptions.py` | ✅ | ConflictError, NotFoundError, ValidationError |
| `dataset_service.py` | ✅ | Slug validation, filtered list |
| `property_service.py` | ✅ | Name validation |
| `project_service.py` | ✅ | N+1 fixed, workflow actions |
| `entry_service.py` | ✅ | Bulk create, external_id validation |
| `task_service.py` | ✅ | Batch UUID fetch, skip helper |
| `candidate_service.py` | ✅ | Accept/reject/bulk actions |
| `audit_service.py` | ✅ | log_action, read-only queries |

### API Utilities

`app/api/utils.py`:
- `get_or_404(service, uuid, entity_name)` - Standardized 404 handling
- `raise_not_found(entity_name)` - Helper for custom 404s
- `handle_conflict_error(error)` - ConflictError → HTTPException

## Key Design Decisions

### 1. N+1 Prevention
List endpoints use JOINs or batch fetching:
- `ProjectService.get_list_with_datasets()` - Single query with JOIN
- `TaskService.get_entry_uuids_for_tasks()` - Batch IN query
- Nested routes use path parameter UUIDs directly

### 2. Domain Exceptions in Services
Services raise domain exceptions (`ConflictError`, `NotFoundError`), routers catch and convert to HTTP responses. Clean separation of concerns.

### 3. Validation in Services
`create_with_validation()` and `update_with_validation()` methods encapsulate uniqueness checks, keeping routers thin.

### 4. SQLite Test Compatibility
- `conftest.py` patches `SQLiteTypeCompiler.visit_JSONB` to render as JSON
- Schema validators handle JSON strings from SQLite
- All models explicitly imported before `create_all`

### 5. Nested URL Structure
- `/datasets/{uuid}/entries[/{uuid}]`
- `/projects/{uuid}/tasks[/{uuid}]`
- `/tasks/{uuid}` as shortcut alias (per Q15)

## Key Design Decisions (old)

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

## Test Infrastructure

```
tests/test_api/
├── test_datasets.py    # 7 tests
├── test_entries.py     # 6 tests
├── test_health.py      # 2 tests
├── test_projects.py    # 7 tests
├── test_properties.py  # 7 tests
└── test_tasks.py       # 7 tests
```

Run: `cd backend && .venv\Scripts\pytest tests/ -v`

## File Structure (Updated)

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py         # DbSession, Pagination dependencies
│   │   ├── utils.py        # get_or_404, error handlers
│   │   └── v1/
│   │       ├── __init__.py # Router aggregation
│   │       ├── datasets.py
│   │       ├── entries.py
│   │       ├── projects.py
│   │       ├── properties.py
│   │       └── tasks.py
│   ├── models/             # 9 ORM models
│   ├── schemas/            # 9 entity + common schemas
│   └── services/
│       ├── __init__.py
│       ├── base.py         # BaseService generic CRUD
│       ├── exceptions.py   # Domain exceptions
│       ├── dataset_service.py
│       ├── entry_service.py
│       ├── project_service.py
│       ├── property_service.py
│       └── task_service.py
└── tests/
```

## Next Steps (for new session)

1. **Verify all tests pass**: `cd backend && .venv\Scripts\pytest -v`
2. **Continue with Candidates**: Create `candidate_service.py` and `candidates.py` router
3. **Reference**: [docs/API_SPECIFICATION_v2.md](docs/API_SPECIFICATION_v2.md) for endpoint specs
4. **Pattern to follow**: Copy structure from `tasks.py` router

## Common Commands

```powershell
# Activate environment
cd backend
.venv\Scripts\activate

# Run all tests
.venv\Scripts\pytest -v

# Run specific test file
.venv\Scripts\pytest tests/test_api/test_tasks.py -v

# Start dev server
.venv\Scripts\uvicorn app.main:app --reload

# Check import
.venv\Scripts\python -c "from app.main import app; print('OK')"
```
