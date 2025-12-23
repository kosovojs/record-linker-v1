# Record Linker - API Specification (Phase 5)

> **Version**: 1.0 (Draft)
> **Last Updated**: 2025-12-23
> **Status**: Awaiting User Review

This document outlines the proposed API endpoints for the Record Linker backend. It is designed based on analysis of the existing models, schemas, and workflow requirements from `PROJECT_CONTEXT.md` and `MODEL_SCHEMA.md`.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Base URL & Response Format](#base-url--response-format)
3. [Core API Endpoints](#core-api-endpoints)
4. [Workflow-Oriented Endpoints](#workflow-oriented-endpoints)
5. [Bulk Operations](#bulk-operations)
6. [Export Endpoints](#export-endpoints)
7. [Implementation Questions](#implementation-questions)
8. [Implementation Plan](#implementation-plan)
9. [Verification Plan](#verification-plan)

---

## Design Principles

Based on existing design decisions from the project context:

| Principle | Implementation |
|-----------|----------------|
| **Public IDs** | Always use `uuid` in URLs and responses. Never expose internal `id`. |
| **Nested Resources** | Tasks under Projects, Candidates under Tasks for clear ownership. |
| **Soft Delete** | `DELETE` operations set `deleted_at`, not hard delete (except AuditLog). |
| **Pagination** | Cursor-based for large lists, offset-based for small ones. |
| **Audit Trail** | All significant actions logged automatically. |

---

## Base URL & Response Format

**Base URL**: `/api/v1`

### Standard Response Structures

```json
// Success (single item)
{
  "uuid": "...",
  "name": "...",
  ...
}

// Success (paginated list)
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_more": true
}

// Error
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error description",
      "type": "value_error"
    }
  ]
}
```

---

## Core API Endpoints

These are the fundamental CRUD operations for each entity.

---

### 1. Datasets

Datasets represent external data sources (e.g., EliteProspects players database).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/datasets` | List all datasets |
| `POST` | `/datasets` | Create a new dataset |
| `GET` | `/datasets/{uuid}` | Get a single dataset |
| `PATCH` | `/datasets/{uuid}` | Update a dataset |
| `DELETE` | `/datasets/{uuid}` | Soft delete a dataset |

#### `GET /datasets`

**Query Parameters:**
- `page` (int, optional, default: 1)
- `page_size` (int, optional, default: 20, max: 100)
- `source_type` (string, optional): Filter by source type
- `entity_type` (string, optional): Filter by entity type
- `search` (string, optional): Search in name/description

**Response:** `PaginatedResponse[DatasetRead]`

#### `POST /datasets`

**Request Body:** `DatasetCreate`
```json
{
  "name": "EliteProspects Players",
  "slug": "eliteprospects-players",
  "description": "Player profiles from EliteProspects.com",
  "source_url": "https://www.eliteprospects.com",
  "source_type": "web_scrape",
  "entity_type": "person"
}
```

**Response (201):** `DatasetRead`

---

### 2. Dataset Entries

Entries are individual records within a dataset (e.g., one person profile).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/datasets/{dataset_uuid}/entries` | List entries in a dataset |
| `POST` | `/datasets/{dataset_uuid}/entries` | Create an entry |
| `GET` | `/datasets/{dataset_uuid}/entries/{uuid}` | Get a single entry |
| `PATCH` | `/datasets/{dataset_uuid}/entries/{uuid}` | Update an entry |
| `DELETE` | `/datasets/{dataset_uuid}/entries/{uuid}` | Soft delete an entry |

#### `GET /datasets/{dataset_uuid}/entries`

**Query Parameters:**
- `page` (int, optional, default: 1)
- `page_size` (int, optional, default: 50, max: 200)
- `search` (string, optional): Search in display_name, external_id
- `has_properties` (bool, optional): Filter entries with/without properties

**Response:** `PaginatedResponse[DatasetEntryRead]`

#### `POST /datasets/{dataset_uuid}/entries` (Bulk)

**Request Body:** `list[DatasetEntryCreate]` (without `dataset_uuid` in body)
```json
[
  {
    "external_id": "ep-12345",
    "display_name": "Wayne Gretzky",
    "external_url": "https://www.eliteprospects.com/player/12345",
    "raw_data": { "name": "Wayne Gretzky", "birth_date": "1961-01-26" }
  }
]
```

**Response (201):** `list[DatasetEntryRead]`

---

### 3. Property Definitions

Global property definitions for the EAV pattern.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/properties` | List all property definitions |
| `POST` | `/properties` | Create a property definition |
| `GET` | `/properties/{uuid}` | Get a single property definition |
| `PATCH` | `/properties/{uuid}` | Update a property definition |
| `DELETE` | `/properties/{uuid}` | Soft delete a property definition |

#### `GET /properties`

**Query Parameters:**
- `page` (int, optional, default: 1)
- `page_size` (int, optional, default: 50)
- `data_type` (string, optional): Filter by data_type_hint
- `searchable_only` (bool, optional): Only searchable properties
- `wikidata_only` (bool, optional): Only properties with wikidata_property

**Response:** `PaginatedResponse[PropertyDefinitionRead]`

---

### 4. Dataset Entry Properties

EAV values attached to dataset entries.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/entries/{entry_uuid}/properties` | List properties for an entry |
| `POST` | `/entries/{entry_uuid}/properties` | Add property values |
| `PATCH` | `/entries/{entry_uuid}/properties/{uuid}` | Update a property value |
| `DELETE` | `/entries/{entry_uuid}/properties/{uuid}` | Remove a property value |

#### `POST /entries/{entry_uuid}/properties` (Bulk)

**Request Body:** `list[DatasetEntryPropertyCreate]`
```json
[
  {
    "property_uuid": "...",
    "value": "1961-01-26",
    "value_normalized": "1961-01-26",
    "confidence": 100,
    "source": "import"
  }
]
```

**Response (201):** `list[DatasetEntryPropertyRead]`

---

### 5. Projects

Reconciliation projects that link datasets to work units.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects` | List projects |
| `POST` | `/projects` | Create a project |
| `GET` | `/projects/{uuid}` | Get project details |
| `PATCH` | `/projects/{uuid}` | Update a project |
| `DELETE` | `/projects/{uuid}` | Soft delete a project |

#### `GET /projects`

**Query Parameters:**
- `page` (int, optional, default: 1)
- `page_size` (int, optional, default: 20)
- `status` (string, optional): Filter by project status
- `dataset_uuid` (uuid, optional): Filter by dataset
- `owner_uuid` (uuid, optional): Filter by owner

**Response:** `PaginatedResponse[ProjectRead]`

#### `GET /projects/{uuid}`

**Response:** `ProjectRead` with optional expansion

**Query Parameters:**
- `include_stats` (bool, optional, default: true): Include task statistics

---

### 6. Tasks

Tasks link projects to dataset entries (unit of work for matching).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects/{project_uuid}/tasks` | List tasks in a project |
| `POST` | `/projects/{project_uuid}/tasks` | Create tasks |
| `GET` | `/projects/{project_uuid}/tasks/{uuid}` | Get a single task |
| `PATCH` | `/projects/{project_uuid}/tasks/{uuid}` | Update a task |
| `DELETE` | `/projects/{project_uuid}/tasks/{uuid}` | Soft delete a task |

#### `GET /projects/{project_uuid}/tasks`

**Query Parameters:**
- `page` (int, optional, default: 1)
- `page_size` (int, optional, default: 50, max: 200)
- `status` (string, optional): Filter by task status
- `has_candidates` (bool, optional): Filter by candidate presence
- `has_accepted` (bool, optional): Filter by accepted match
- `min_score` (int, optional): Minimum highest_score
- `sort` (string, optional): `created_at`, `highest_score`, `status`
- `order` (string, optional): `asc`, `desc`

**Response:** `PaginatedResponse[TaskRead]`

---

### 7. Match Candidates

Potential Wikidata matches for tasks.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks/{task_uuid}/candidates` | List candidates for a task |
| `POST` | `/tasks/{task_uuid}/candidates` | Create candidates |
| `GET` | `/tasks/{task_uuid}/candidates/{uuid}` | Get a single candidate |
| `PATCH` | `/tasks/{task_uuid}/candidates/{uuid}` | Update a candidate (accept/reject) |
| `DELETE` | `/tasks/{task_uuid}/candidates/{uuid}` | Soft delete a candidate |

#### `GET /tasks/{task_uuid}/candidates`

**Query Parameters:**
- `status` (string, optional): Filter by candidate status
- `source` (string, optional): Filter by candidate source
- `min_score` (int, optional): Minimum score
- `sort` (string, optional): `score`, `created_at`
- `order` (string, optional): `asc`, `desc` (default: `desc` for score)

**Response:** `list[MatchCandidateRead]` (not paginated - typically few per task)

---

### 8. Audit Logs

Read-only audit trail (no create/update/delete via API).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/audit-logs` | List audit logs (admin only) |
| `GET` | `/audit-logs/{uuid}` | Get a single audit log entry |

#### `GET /audit-logs`

**Query Parameters:**
- `page` (int, optional, default: 1)
- `page_size` (int, optional, default: 50)
- `entity_type` (string, optional): Filter by entity type
- `entity_uuid` (uuid, optional): Filter by entity
- `action` (string, optional): Filter by action
- `user_uuid` (uuid, optional): Filter by user
- `from_date` (datetime, optional): Start of date range
- `to_date` (datetime, optional): End of date range

**Response:** `PaginatedResponse[AuditLogRead]`

---

## Workflow-Oriented Endpoints

These endpoints support the reconciliation workflow beyond basic CRUD.

---

### Project Lifecycle

#### `POST /projects/{uuid}/start`

Start processing a project (transition from `draft` → `active` → `pending_search`).

**Request Body:**
```json
{
  "entry_uuids": ["...", "..."],  // Optional: specific entries to include
  "search_strategies": ["wikidata_api", "sparql"]  // Optional: override config
}
```

**Response (202):**
```json
{
  "message": "Project started with 150 tasks created",
  "tasks_created": 150
}
```

---

#### `POST /projects/{uuid}/rerun`

Re-run processing for specific criteria (inspired by v1.md).

**Request Body:**
```json
{
  "criteria": "no_candidates",  // or "failed", "no_accepted"
  "task_uuids": ["..."]  // Optional: specific tasks
}
```

**Response (202):**
```json
{
  "message": "Scheduled 25 tasks for reprocessing",
  "tasks_reset": 25
}
```

---

#### `GET /projects/{uuid}/stats`

Get detailed project statistics.

**Response:**
```json
{
  "project_uuid": "...",
  "total_tasks": 500,
  "by_status": {
    "new": 10,
    "awaiting_review": 350,
    "reviewed": 100,
    "failed": 5,
    ...
  },
  "candidates": {
    "total": 1200,
    "accepted": 100,
    "rejected": 50
  },
  "avg_highest_score": 75.5,
  "review_progress_percent": 20.0
}
```

---

### Task Workflow

#### `POST /projects/{project_uuid}/tasks/{uuid}/skip`

Skip a task (shortcut for status update to `skipped`).

**Response (200):** `TaskRead`

---

#### `POST /tasks/{task_uuid}/candidates/{uuid}/accept`

Accept a candidate (transition candidate to `accepted`, task to `reviewed`).

**Response (200):**
```json
{
  "task": { /* TaskRead */ },
  "candidate": { /* MatchCandidateRead */ }
}
```

---

#### `POST /tasks/{task_uuid}/candidates/{uuid}/reject`

Reject a candidate.

**Response (200):** `MatchCandidateRead`

---

### Wikidata Search

#### `GET /wikidata/search`

Search Wikidata for potential matches (for manual candidate addition).

**Query Parameters:**
- `query` (string, required): Search query
- `type` (string, optional): Entity type (person, organization, etc.)
- `limit` (int, optional, default: 10)

**Response:**
```json
{
  "results": [
    {
      "qid": "Q5879",
      "label": "Johann Wolfgang von Goethe",
      "description": "German writer and statesman",
      "aliases": ["Goethe", "J.W. von Goethe"]
    }
  ]
}
```

---

## Bulk Operations

Endpoints for efficient batch processing.

---

### `POST /datasets/{dataset_uuid}/entries/import`

Bulk import entries from file upload.

**Request:** `multipart/form-data`
- `file`: CSV or JSON file
- `mapping`: JSON mapping configuration

**Response (202):**
```json
{
  "message": "Successfully queued 1500 entries for import",
  "entries_queued": 1500,
  "job_id": "..."  // For status tracking
}
```

---

### `POST /projects/{project_uuid}/tasks/bulk`

Bulk create tasks from entry UUIDs.

**Request Body:**
```json
{
  "entry_uuids": ["...", "..."],
  "all_entries": false  // If true, include all dataset entries
}
```

**Response (201):**
```json
{
  "tasks_created": 150,
  "skipped_duplicates": 5
}
```

---

### `PATCH /tasks/{task_uuid}/candidates/bulk`

Bulk update candidates (e.g., reject all except accepted).

**Request Body:**
```json
{
  "candidate_uuids": ["...", "..."],
  "updates": {
    "status": "rejected"
  }
}
```

**Response (200):** `list[MatchCandidateRead]`

---

## Export Endpoints

---

### `GET /projects/{uuid}/export`

Export project results.

**Query Parameters:**
- `format` (string, required): `csv`, `json`, `ndjson`
- `status` (string, optional): Only tasks with specific status
- `include_rejected` (bool, optional, default: false)

**Response:** File download with appropriate Content-Type

---

### `GET /projects/{uuid}/approved-matches`

Get all accepted candidates for a project (for quick export).

**Response:**
```json
{
  "matches": [
    {
      "task_uuid": "...",
      "entry_external_id": "ep-12345",
      "entry_display_name": "Wayne Gretzky",
      "wikidata_id": "Q5879",
      "score": 95,
      "reviewed_at": "2025-12-23T10:00:00Z"
    }
  ],
  "total": 100
}
```

---

## Implementation Questions

> **Instructions**: Please answer these questions by editing this file directly. Your answers will guide the implementation.

---

### Q1: Authentication & Authorization

The reference `v1.md` includes authentication endpoints. Do we need authentication for this phase, or should we defer it?

**Options:**
- A) Implement full authentication now (session-based like v1.md)
- B) Implement simple API key authentication
- C) Defer authentication - all endpoints open for now
- D) Other: _____________

**Your Answer:**

---

### Q2: User Assignment

The models have `owner_id` on Project and `reviewed_by_id` on Task. How should these work?

**Options:**
- A) Require user UUID in request (frontend knows current user)
- B) Extract from authentication context (implies need for auth)
- C) Default to a system user for now, implement properly later
- D) Make user fields optional (nullable) for now

**Your Answer:**

---

### Q3: Task Creation Scope

When creating a project, should tasks be:

**Options:**
- A) Created automatically for ALL entries in the dataset
- B) Created explicitly via separate endpoint (POST /projects/{uuid}/tasks)
- C) Created during project start (POST /projects/{uuid}/start) with optional filter
- D) Combination - optional auto-create flag on project creation

**Your Answer:**

---

### Q4: Candidate Auto-Acceptance

The ProjectConfig has `auto_accept_threshold`. When a candidate exceeds this score:

**Options:**
- A) Auto-accept during candidate creation (in API layer)
- B) Auto-accept in background job (separate service)
- C) Mark for auto-acceptance, but require confirmation
- D) Defer this feature for now

**Your Answer:**

---

### Q5: Wikidata Integration

The `/wikidata/search` endpoint implies calling external Wikidata API. Should this be:

**Options:**
- A) Implemented in Phase 5 (blocking HTTP calls to Wikidata)
- B) Deferred to Phase 6 (Services layer)
- C) Implemented as a stub that returns mock data for now
- D) Other: _____________

**Your Answer:**

---

### Q6: Dataset Entry Properties URL Structure

Currently proposed as `/entries/{entry_uuid}/properties`. Alternative:

**Options:**
- A) Keep as proposed: `/entries/{entry_uuid}/properties` (flat)
- B) Nest under datasets: `/datasets/{dataset_uuid}/entries/{entry_uuid}/properties`
- C) Both routes (A as shortcut, B as canonical)

**Your Answer:**

---

### Q7: Audit Log Creation

Should audit logs be created:

**Options:**
- A) Automatically via SQLAlchemy event hooks (model layer)
- B) Explicitly in service layer methods
- C) Via FastAPI middleware (request/response level)
- D) Combination - different strategies for different actions

**Your Answer:**

---

### Q8: Pagination Style

For lists larger than ~100 items:

**Options:**
- A) Offset-based (page/page_size) - simpler, sufficient for this scale
- B) Cursor-based (cursor/limit) - more robust for large datasets
- C) Both supported (caller's choice)

**Your Answer:**

---

### Q9: Candidate Deduplication

Per MODEL_SCHEMA.md, same Wikidata QID can appear multiple times for a task (different sources). Should we:

**Options:**
- A) Keep as-is (allow duplicates, let user see all sources)
- B) Deduplicate in response (merge sources, show highest score)
- C) Prevent duplicate creation (return existing if same QID)

**Your Answer:**

---

### Q10: Error Handling for Bulk Operations

When bulk creating/updating and some items fail:

**Options:**
- A) All-or-nothing (transaction rollback on any error)
- B) Partial success (return successful items + error details)
- C) Configurable via request parameter

**Your Answer:**

---

### Q11: Status Transition Validation

Should the API enforce valid state transitions (per MODEL_SCHEMA.md state machines)?

**Options:**
- A) Yes, strict enforcement with clear error messages
- B) Yes, but allow admin override
- C) No, trust clients to send valid transitions
- D) Warn but allow invalid transitions (for flexibility during dev)

**Your Answer:**

---

### Q12: Project Stats Computation

For `GET /projects/{uuid}/stats`:

**Options:**
- A) Compute on the fly (accurate but potentially slow)
- B) Use denormalized counters only (fast but may drift)
- C) Compute on the fly, but cache for X minutes
- D) Use denormalized counters + periodic sync job

**Your Answer:**

---

### Q13: File Import Format

For `POST /datasets/{dataset_uuid}/entries/import`:

**Options:**
- A) Support CSV only (simpler, most common)
- B) Support JSON and CSV
- C) Support JSON, CSV, and NDJSON (newline-delimited JSON)
- D) Defer file import to later phase

**Your Answer:**

---

### Q14: Entry Properties Endpoint Necessity

The `/entries/{entry_uuid}/properties` endpoints manage EAV values. Are these needed for the MVP, or will properties always be imported with entries?

**Options:**
- A) Needed - users will add/edit properties manually
- B) Not needed for MVP - properties come only from import
- C) Read-only needed (GET only), no create/update

**Your Answer:**

---

### Q15: Nested Task Retrieval

Currently tasks are under `/projects/{project_uuid}/tasks/{uuid}`. Sometimes we need to get a task by UUID alone. Should we add:

**Options:**
- A) Keep nested only (must know project)
- B) Add shortcut `/tasks/{uuid}` that redirects or returns directly
- C) Add `/tasks/{uuid}` as alias (same response as nested)

**Your Answer:**

---

## Implementation Plan

> **Note**: This plan will be finalized after questions are answered.

### Phase 5a: Core CRUD Endpoints

**Order of Implementation:**

1. **Datasets** - Foundation, no dependencies
   - Implement router, service, tests

2. **Property Definitions** - No dependencies
   - Implement router, service, tests

3. **Dataset Entries** - Depends on Datasets
   - Implement nested under datasets
   - Bulk creation support

4. **Projects** - Depends on Datasets
   - Implement router, service, tests
   - Include stats endpoint

5. **Tasks** - Depends on Projects, Dataset Entries
   - Implement nested under projects
   - Include filtering

6. **Match Candidates** - Depends on Tasks
   - Implement CRUD + accept/reject shortcuts

7. **Audit Logs** - Read-only
   - Query endpoint with filters

### Phase 5b: Workflow & Bulk Endpoints

1. Project lifecycle endpoints (start, rerun)
2. Bulk task creation
3. Bulk candidate updates
4. Export endpoints

### Phase 5c: Wikidata Integration (if not deferred)

1. Wikidata search endpoint
2. Auto-search service integration

---

## Verification Plan

### Automated Tests

All endpoints will have:

1. **Unit tests** for service layer methods
2. **Integration tests** for API endpoints using `httpx` + `pytest-asyncio`

**Test command:**
```powershell
cd backend
.venv\Scripts\pytest tests/test_api/ -v
```

### Manual Verification

After implementation:

1. Start dev server: `.venv\Scripts\uvicorn app.main:app --reload`
2. Access OpenAPI docs at `http://localhost:8000/docs`
3. Test each endpoint manually via Swagger UI
4. Verify audit logs are created for significant actions

---

## Files to Create

Based on phase 5a plan:

```
backend/app/
├── api/
│   └── v1/
│       ├── __init__.py          # Router aggregation
│       ├── datasets.py          # Dataset endpoints
│       ├── properties.py        # PropertyDefinition endpoints
│       ├── entries.py           # DatasetEntry endpoints
│       ├── projects.py          # Project endpoints
│       ├── tasks.py             # Task endpoints
│       ├── candidates.py        # MatchCandidate endpoints
│       └── audit_logs.py        # AuditLog endpoints
├── services/
│   ├── __init__.py
│   ├── dataset_service.py
│   ├── entry_service.py
│   ├── property_service.py
│   ├── project_service.py
│   ├── task_service.py
│   ├── candidate_service.py
│   └── audit_service.py
```

---

## Appendix: Related Design Concerns

### Concern 1: URL Design Alternatives

I'm proposing nested URLs for clarity but they can be verbose:

| Proposed | Alternative |
|----------|-------------|
| `/projects/{project}/tasks/{task}` | `/tasks/{task}` with project in query param |
| `/tasks/{task}/candidates/{candidate}` | `/candidates/{candidate}` |
| `/datasets/{dataset}/entries/{entry}` | `/entries/{entry}` |

**Current decision:** Use nested for clarity and ownership enforcement.

### Concern 2: Response Expansion

Should related objects be expandable in response? Example:

```
GET /projects/{uuid}/tasks/{uuid}?expand=entry,candidates
```

This could reduce round-trips but adds complexity.

**Current decision:** Start simple, add if needed.

### Concern 3: Async Job Tracking

File imports and project start operations may be async. Should we add job tracking?

```
POST /datasets/{uuid}/entries/import → returns job_id
GET /jobs/{job_id} → returns job status
```

**Current decision:** Defer to later phase unless synchronous operations become problematic.

---

*End of API Specification Document*
