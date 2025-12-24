# FastAPI Backend Code Review

**Date**: 2024-12-24
**Reviewer**: AI Code Review
**Scope**: All models, services, API routers, schemas, and configuration

---

## Executive Summary

The codebase demonstrates solid foundational patterns: proper use of async/await, type hints, Pydantic schemas, and SQLModel. However, there are several issues that would be flagged in a senior-level code review, ranging from N+1 query patterns to DRY violations and missing business logic enforcement.

---

## Critical Issues

### 1. N+1 Query in `start_project()` Method

**File**: [project_service.py](backend/app/services/project_service.py#L188-L199)

**Problem**: The loop checks for existing tasks one-by-one inside the entry loop, causing N database queries.

```python
for entry in entries:
    existing_stmt = select(Task).where(
        Task.project_id == project.id,
        Task.dataset_entry_id == entry.id,
        Task.deleted_at.is_(None),
    )
    existing = await self.db.execute(existing_stmt)
    if existing.scalar_one_or_none() is None:
        # create task...
```

**Fix**: Batch-fetch all existing task entry IDs upfront:

```python
# Fetch all existing entry IDs in one query
existing_stmt = select(Task.dataset_entry_id).where(
    Task.project_id == project.id,
    Task.deleted_at.is_(None),
)
result = await self.db.execute(existing_stmt)
existing_entry_ids = set(result.scalars().all())

# Then filter in Python
for entry in entries:
    if entry.id not in existing_entry_ids:
        # create task...
```

---

### 2. N+1 Query in `bulk_create_for_dataset()` Method

**File**: [entry_service.py](backend/app/services/entry_service.py#L82-L108)

**Problem**: Similar issue - checking for existing external_id one-by-one in a loop.

```python
for data in entries:
    existing = await self.get_by_external_id(dataset.id, data.external_id)
    if existing:
        raise ConflictError(...)
```

**Fix**: Batch-fetch all existing external IDs:

```python
external_ids = [e.external_id for e in entries]
existing_stmt = select(DatasetEntry.external_id).where(
    DatasetEntry.dataset_id == dataset.id,
    DatasetEntry.external_id.in_(external_ids),
    DatasetEntry.deleted_at.is_(None),
)
result = await self.db.execute(existing_stmt)
existing_ids = set(result.scalars().all())

conflicts = [eid for eid in external_ids if eid in existing_ids]
if conflicts:
    raise ConflictError("Entry", "external_id", conflicts[0])
```

---

### 3. Post-Filtering in Python Instead of SQL

**File**: [task_service.py](backend/app/services/task_service.py#L95-L111)

**Problem**: Filters like `has_candidates`, `has_accepted`, `min_score` are applied in Python after fetching data, which:
- Returns incorrect `total` count
- Fetches more data than needed
- Breaks pagination

```python
items, total = await self.get_list(pagination, filters)

# Post-filtering for boolean conditions
if has_candidates is not None:
    if has_candidates:
        items = [t for t in items if t.candidate_count > 0]
```

**Fix**: Apply all filters at the SQL level in `get_list_for_project()`.

---

**File**: [property_service.py](backend/app/services/property_service.py#L51-L57)

**Problem**: Same issue with `wikidata_only` filter:

```python
if wikidata_only:
    items = [item for item in items if item.wikidata_property is not None]
```

---

### 4. Missing `updated_at` Timestamp Updates

**File**: [base.py (service)](backend/app/services/base.py#L114-L130)

**Problem**: The `update()` method does not update the `updated_at` timestamp.

```python
async def update(self, db_obj: ModelType, data: UpdateSchemaType) -> ModelType:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    # Missing: db_obj.updated_at = utc_now()
```

**Fix**: Add timestamp update:

```python
from app.models.base import utc_now

async def update(...):
    # ... existing logic ...
    db_obj.updated_at = utc_now()
    self.db.add(db_obj)
```

---

## Moderate Issues

### 5. Hardcoded String for Enum Value

**File**: [task_service.py](backend/app/services/task_service.py#L169-L175)

**Problem**: Uses hardcoded string instead of the enum constant:

```python
async def skip_task(self, task: Task) -> Task:
    task.status = "skipped"  # Should be TaskStatus.SKIPPED
```

**Fix**:

```python
from app.schemas.enums import TaskStatus

task.status = TaskStatus.SKIPPED
```

---

### 6. Incomplete AcceptRejectResponse Data

**File**: [candidates.py](backend/app/api/v1/candidates.py#L304-L314)

**Problem**: Returns `None` for `project_uuid` and `dataset_entry_uuid` with a comment acknowledging this:

```python
return AcceptRejectResponse(
    task=TaskReadWithValidator(
        **updated_task.model_dump(),
        project_uuid=None,  # Would need to fetch project
        dataset_entry_uuid=None,  # Would need to fetch entry
    ),
```

**Fix**: Fetch the related UUIDs using existing service methods or a single join query.

---

### 7. Deprecated `datetime.utcnow()` Usage

**File**: [audit_log.py](backend/app/models/audit_log.py#L47-L49)

**Problem**: Uses deprecated `datetime.utcnow()`:

```python
created_at: datetime = Field(
    default_factory=datetime.utcnow,  # Deprecated in Python 3.12
```

**Fix**: Use the project's existing `utc_now()` function:

```python
from app.models.base import utc_now

created_at: datetime = Field(default_factory=utc_now)
```

---

### 8. Services Manually Instantiated in Routers

**Files**: All API router files

**Problem**: Services are manually instantiated inside each endpoint:

```python
@router.get("/{uuid}")
async def get_project(db: DbSession, uuid: UUID):
    service = ProjectService(db)  # Manual instantiation
```

**Better Pattern**: Use FastAPI dependency injection for services:

```python
# In deps.py
def get_project_service(db: DbSession) -> ProjectService:
    return ProjectService(db)

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]

# In router
@router.get("/{uuid}")
async def get_project(
    service: ProjectServiceDep,
    uuid: UUID,
):
    project = await service.get_by_uuid(uuid)
```

---

### 9. DRY Violation: Duplicated SQLite JSON Validators

**Files**:
- [tasks.py](backend/app/api/v1/tasks.py#L36-L48)
- [candidates.py](backend/app/api/v1/candidates.py#L38-L97)
- [entries.py](backend/app/api/v1/entries.py#L31-L43)

**Problem**: Each router defines its own `*WithValidator` class with nearly identical JSON parsing validators.

**Fix**: Create a shared validator mixin or factory function:

```python
# In schemas/mixins.py
def sqlite_json_validator(field_name: str):
    @field_validator(field_name, mode="before")
    @classmethod
    def parse_json(cls, v):
        if v is None:
            return {} if field_name == "extra_data" else None
        if isinstance(v, str):
            return json.loads(v)
        return v
    return parse_json
```

---

### 10. Missing Exception Handler Registration

**Files**: [main.py](backend/app/main.py), [exceptions.py](backend/app/services/exceptions.py)

**Problem**: Service exceptions are defined but not registered as global exception handlers. Each router manually catches and converts them:

```python
try:
    # service operation
except ConflictError as e:
    handle_conflict_error(e)
```

**Better Pattern**: Register global exception handlers in `main.py`:

```python
@app.exception_handler(ConflictError)
async def conflict_exception_handler(request, exc):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )
```

---

### 11. Inconsistent Return Type on `get_or_404`

**File**: [utils.py](backend/app/api/utils.py#L28-L42)

**Problem**: The function has no return type annotation, and uses a generic `BaseService` which loses type information:

```python
async def get_or_404(
    service: BaseService,  # Generic type lost
    uuid: UUID,
    entity_name: str,
):  # No return type
```

**Fix**: Add proper generic typing:

```python
from typing import TypeVar

T = TypeVar("T")

async def get_or_404(
    service: BaseService[T, Any, Any],
    uuid: UUID,
    entity_name: str,
) -> T:
```

---

## Minor Issues

### 12. CORS Configuration Too Permissive

**File**: [main.py](backend/app/main.py#L36-L42)

**Problem**: `allow_origins=["*"]` is too permissive for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Too permissive
```

**Fix**: Use environment-based configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # From config
```

---

### 13. Late Import in main.py

**File**: [main.py](backend/app/main.py#L62-L65)

**Problem**: Import at bottom of file, after app instantiation:

```python
# API v1 router
from app.api.v1 import api_router  # Late import

app.include_router(api_router, prefix=settings.api_v1_prefix)
```

**Fix**: Move import to top of file with other imports.

---

### 14. Unused `search` Parameter

**Files**:
- [dataset_service.py](backend/app/services/dataset_service.py#L34-L49) - `search` parameter is accepted but not used
- [entry_service.py](backend/app/services/entry_service.py#L38-L46) - same issue

**Problem**: The `search` parameter is defined but the implementation is missing:

```python
async def get_list_filtered(
    self,
    pagination: PaginationParams,
    source_type: str | None = None,
    entity_type: str | None = None,
    search: str | None = None,  # Never used
) -> tuple[list[Dataset], int]:
```

---

### 15. `has_more` Computation Duplication

**Files**: All paginated API responses

**Problem**: `has_more` is computed in every endpoint:

```python
has_more=(pagination.page * pagination.page_size) < total,
```

But `PaginatedResponse` already has `has_next` property which does the same thing.

**Fix**: Use the schema's built-in property or make it a required field that's auto-computed.

---

### 16. Potential Data Integrity Issue in `soft_delete`

**File**: [base.py (service)](backend/app/services/base.py#L132-L139)

**Problem**: Soft deleting a parent (e.g., Project) doesn't cascade to children (Tasks, Candidates). This can leave orphaned active children pointing to a deleted parent.

**Fix**: Either:
1. Add cascade soft-delete logic
2. Document this as expected behavior
3. Add validation in child queries to check parent deletion status

---

### 17. Missing Index for Soft Delete Queries

**Files**: All model files

**Problem**: Most queries filter by `deleted_at IS NULL`, but there's no index on `deleted_at`. For large tables, this could be slow.

**Fix**: Add partial index or composite indexes that include `deleted_at`:

```python
__table_args__ = (
    Index("idx_projects_active", "id", postgresql_where=text("deleted_at IS NULL")),
)
```

---

### 18. Docstrings Reference Non-Existent Relationship Attributes

**Files**: Multiple model files (e.g., property_definition.py, user.py)

**Problem**: Comments mention relationships that don't exist:

```python
# Note: Relationship to values is accessed via queries
```

This is fine as documentation, but could be misleading if someone expects SQLAlchemy relationships.

---

## Architecture Recommendations

### Consider Repository Pattern

The current service layer combines business logic with data access. For larger projects, consider separating:
- **Repository**: Pure data access (CRUD operations)
- **Service**: Business logic and orchestration

### Consider Unit of Work Pattern

Multiple operations within a single endpoint sometimes manage their own commits. A Unit of Work pattern would provide better transaction control.

### Add Response Model Validation

Consider enabling `response_model_validate=True` in FastAPI config to catch response schema mismatches early.

---

## Summary Table

| Severity | Issue | Location |
|----------|-------|----------|
| 🔴 Critical | N+1 query (start_project) | project_service.py:188-199 |
| 🔴 Critical | N+1 query (bulk_create) | entry_service.py:82-108 |
| 🔴 Critical | Post-filtering breaks pagination | task_service.py:95-111 |
| 🔴 Critical | Missing updated_at updates | base.py (service):114-130 |
| 🟡 Moderate | Hardcoded enum string | task_service.py:171 |
| 🟡 Moderate | Incomplete response data | candidates.py:304-314 |
| 🟡 Moderate | Deprecated datetime.utcnow | audit_log.py:47-49 |
| 🟡 Moderate | Manual service instantiation | All routers |
| 🟡 Moderate | DRY violation (validators) | tasks.py, candidates.py, entries.py |
| 🟡 Moderate | Missing exception handlers | main.py |
| 🟡 Moderate | No return type on get_or_404 | utils.py:28-42 |
| 🟢 Minor | Permissive CORS | main.py:36-42 |
| 🟢 Minor | Late import | main.py:62-65 |
| 🟢 Minor | Unused search parameter | dataset_service.py, entry_service.py |
| 🟢 Minor | has_more duplication | All routers |
| 🟢 Minor | Missing cascade soft-delete | base.py (service) |
| 🟢 Minor | Missing deleted_at indexes | All models |
