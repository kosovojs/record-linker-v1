# FastAPI Backend Code Review

**Date:** 2024-12-24
**Reviewer:** Code Review
**Scope:** Complete backend codebase (`app/` directory)

---

## Critical Issues

### 1. Soft-Delete Cascade Not Implemented

**Location:** `app/services/base.py:136-150`

The `soft_delete` method explicitly warns that cascading is not handled, but no cascade logic is implemented anywhere:

```python
# WARNING: This does NOT cascade to child records. If you delete a parent
# entity (e.g., Project), child entities (e.g., Tasks, Candidates) will
# remain active but point to a deleted parent.
```

**Problem:** Deleting a Project leaves orphaned Tasks and Candidates that still appear in queries but have no valid parent. This breaks referential integrity at the application level.

**Recommendation:**
- Implement cascade soft-delete in `ProjectService.soft_delete()` that also soft-deletes related Tasks and Candidates
- Or implement a database trigger / scheduled cleanup job
- At minimum, filter child queries to exclude records where parent is soft-deleted

---

### 2. Double Commit Pattern in `get_db` Dependency

**Location:** `app/database.py:29-37`

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()  # <-- Commits here
        except Exception:
            await session.rollback()
            raise
```

**Problem:** Services also call `commit()` after their operations (see `base.py:109`, `base.py:131`, etc.). This means:
1. Service commits the transaction
2. `get_db` tries to commit again (redundant)
3. If an exception occurs between service commit and `get_db` commit, transaction state is inconsistent

**Recommendation:** Choose one strategy:
- **Option A:** Remove commits from services, let `get_db` handle all commits (clean but requires careful error handling)
- **Option B:** Remove commit from `get_db`, make it services' responsibility to commit (current mixed approach)

---

### 3. Missing Relationship Validation for Nested Resources

**Location:** Multiple API files (`tasks.py`, `candidates.py`, `entries.py`)

When accessing nested resources like `/tasks/{task_uuid}/candidates/{candidate_uuid}`, the code:
1. Validates that `task_uuid` exists
2. Fetches candidate by `candidate_uuid`
3. **Does NOT verify the candidate belongs to the task**

```python
@router.get("/tasks/{task_uuid}/candidates/{candidate_uuid}")
async def get_candidate(db: DbSession, task_uuid: UUID, candidate_uuid: UUID):
    await get_or_404(task_service, task_uuid, "Task")  # Validates task exists
    candidate = await get_or_404(candidate_service, candidate_uuid, "Candidate")  # No parent check!
```

**Problem:** User can access any candidate by guessing UUIDs, regardless of task ownership.

**Recommendation:** Add parent validation:
```python
if candidate.task_id != task.id:
    raise HTTPException(status_code=404, detail="Candidate not found in this task")
```

---

## Moderate Issues

### 4. Duplicated SQLite JSON Validator Classes

**Location:**
- `app/api/v1/tasks.py:37-48` (`TaskReadWithValidator`)
- `app/api/v1/candidates.py:39-83` (`MatchCandidateReadWithValidator`, `TaskReadWithValidator`)
- `app/api/v1/entries.py:32-42` (`DatasetEntryReadWithValidator`)

**Problem:**
1. Same workaround copy-pasted across 3+ files
2. `TaskReadWithValidator` is defined twice (in `tasks.py` and `candidates.py`)
3. SQLite-specific handling shouldn't be in API layer

**Recommendation:**
- Create a `app/schemas/validators.py` module with reusable mixins/validators
- Or implement at the model level using SQLModel's `@field_serializer`
- Consider if SQLite support is even needed (config says PostgreSQL)

---

### 5. Service Factory Functions Are Unused

**Location:**
- `app/services/project_service.py:391-393`
- `app/services/task_service.py:205-207`
- All service files have `get_*_service()` factory functions

```python
def get_project_service(db: AsyncSession) -> ProjectService:
    """Factory function for ProjectService."""
    return ProjectService(db)
```

**Problem:** These factory functions are never used. All API routes instantiate services directly:
```python
service = ProjectService(db)  # Direct instantiation everywhere
```

**Recommendation:**
- Either use the factory functions consistently (as FastAPI dependencies)
- Or remove them to reduce dead code

---

### 6. Inline Imports in `__init__.py` Creates Maintenance Burden

**Location:** `app/models/__init__.py:36-83`

```python
def __getattr__(name: str):
    if name == "BaseTableModel":
        from app.models.base import BaseTableModel
        return BaseTableModel
    elif name == "User":
        from app.models.user import User
        return User
    # ... 8 more elif blocks
```

**Problem:**
- Every new model requires adding yet another `elif` block
- Easy to forget when adding new models
- Unnecessary complexity when TYPE_CHECKING imports could solve circular imports

**Recommendation:** Use `TYPE_CHECKING` pattern:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .project import Project
    # ...
```

---

### 7. Untyped `dict` Fields for JSONB Data

**Location:** Multiple model files

```python
# In project.py
config: dict = Field(...)  # Should be dict[str, Any]

# In match_candidate.py
score_breakdown: dict | None = Field(...)  # Untypes dict
matched_properties: dict | None = Field(...)
extra_data: dict = Field(...)
```

**Problem:** `dict` without type parameters loses type safety and IDE support.

**Recommendation:** Use `dict[str, Any]` or create typed TypedDict/Pydantic models for JSONB fields.

---

### 8. Pagination Calculation Logic Duplicated

**Location:** Every service file that does pagination

```python
# This pattern appears 6+ times:
offset = (pagination.page - 1) * pagination.page_size
paginated_query = (
    base_query
    .order_by(Model.created_at.desc())
    .offset(offset)
    .limit(pagination.page_size)
)
```

**Problem:**
1. DRY violation - same 5 lines repeated everywhere
2. `PaginationParams` already has an `offset` property that's never used

**Recommendation:** Add helper method to base service or use the existing `offset` property:
```python
offset = pagination.offset  # Use the property!
```

---

### 9. `has_more` Calculated Inconsistently

**Location:** All API routes returning `PaginatedResponse`

```python
# Pattern 1 (API routes):
has_more=(pagination.page * pagination.page_size) < total

# Pattern 2 (could use):
has_more=(offset + len(items)) < total  # More accurate
```

**Problem:** Current calculation can be wrong when `page * page_size` isn't accurate for the last page.

**Recommendation:** Calculate based on actual items returned:
```python
has_more = total > (pagination.offset + len(items))
```

---

### 10. Missing Exception Handler for `InvalidStateTransitionError`

**Location:** `app/services/exceptions.py:50-58` defines the exception, but `app/main.py` has no handler for it.

```python
class InvalidStateTransitionError(ServiceError):
    """Invalid status/state transition."""
    ...
```

**Problem:** If raised, it would fall through to the generic `ServiceError` handler returning 500, when it should likely return 400 or 409.

**Recommendation:** Add dedicated handler:
```python
@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_exception_handler(request: Request, exc: InvalidStateTransitionError):
    return JSONResponse(status_code=409, content={"detail": exc.message})
```

---

## Minor Issues

### 11. `any` Type Used in Generic

**Location:** `app/api/utils.py:28-30`

```python
async def get_or_404[T](
    service: BaseService[T, any, any],  # <-- lowercase 'any' is wrong
    ...
```

**Problem:** `any` (lowercase) is not a valid type hint. Should be `Any` from typing.

---

### 12. Unused Import in `api/utils.py`

**Location:** `app/api/utils.py:17`

```python
T = TypeVar("T")  # Defined but never used (using [T] syntax instead)
```

---

### 13. Request/Response Schemas Defined Inside Router Files

**Location:** `app/api/v1/projects.py:41-98`

```python
class ProjectStartRequest(BaseModel):
    ...
class ProjectStartResponse(BaseModel):
    ...
# ... 5 more schemas
```

**Problem:** Schemas defined inside route files:
- Can't be easily reused
- Makes route files longer than necessary
- Breaks convention (other schemas are in `app/schemas/`)

**Recommendation:** Move to `app/schemas/project.py` or create `app/schemas/workflow.py`.

---

### 14. `updated_at` Not Auto-Updated in Base Model

**Location:** `app/models/base.py:65-66`

```python
created_at: datetime = Field(default_factory=utc_now)
updated_at: datetime = Field(default_factory=utc_now)  # Same factory!
```

**Problem:** `updated_at` is manually updated only in `base.py:128` during service updates. If someone modifies a model directly and commits, `updated_at` won't change.

**Recommendation:** Use SQLAlchemy's `onupdate` parameter:
```python
updated_at: datetime = Field(
    default_factory=utc_now,
    sa_column_kwargs={"onupdate": utc_now}
)
```

---

### 15. Hardcoded Version String

**Location:** `app/main.py:36,89`

```python
version="0.1.0",  # Hardcoded in FastAPI init
# ...
"version": "0.1.0",  # Hardcoded again in root endpoint
```

**Recommendation:** Move to config or read from `pyproject.toml`.

---

### 16. Missing Return Type on `raise_not_found`

**Location:** `app/api/utils.py:20-25`

```python
def raise_not_found(entity_name: str) -> None:
    raise HTTPException(...)
```

**Problem:** Function raises, so return type should be `NoReturn` not `None`.

---

### 17. Enum Values Stored as Strings Without DB Constraint

**Location:** All models using enums (e.g., `task.py:60-63`)

```python
status: TaskStatus = Field(
    default=TaskStatus.NEW,
    sa_column=Column(String(50), nullable=False),  # No CHECK constraint
)
```

**Problem:** Database allows any string, validation only happens at Python level. Bad data can be inserted via raw SQL or migrations.

**Recommendation:** Add CHECK constraint or use PostgreSQL ENUM type:
```python
sa_column=Column(Enum(TaskStatus), nullable=False)
```

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 3 |
| Moderate | 7 |
| Minor | 7 |

### Priority Fixes
1. **Implement nested resource parent validation** (security issue)
2. **Choose single commit strategy** (data integrity)
3. **Implement soft-delete cascade** (referential integrity)
4. **Consolidate SQLite validators** (maintainability)
