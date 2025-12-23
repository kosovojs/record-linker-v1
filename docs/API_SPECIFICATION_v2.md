# Record Linker - API Specification v2

> **Version**: 2.0 (Refined)
> **Last Updated**: 2025-12-23
> **Status**: Awaiting Final Review

This refined specification incorporates all decisions from the Q&A phase, removing deferred features and focusing on what will be implemented in Phase 5.

---

## Design Decisions Summary

| Aspect | Decision |
|--------|----------|
| **Authentication** | Deferred - all endpoints open |
| **User fields** | Nullable (`owner_uuid`, `reviewed_by_uuid` optional) |
| **Pagination** | Offset-based (`page`, `page_size`) |
| **Bulk errors** | All-or-nothing (transaction rollback) |
| **State transitions** | Strict validation + admin override flag |
| **Stats computation** | On-the-fly (no caching) |

---

## Base URL & Conventions

**Base URL**: `/api/v1`

**Common Patterns**:
- All paths use UUIDs, never internal IDs
- `DELETE` = soft delete (sets `deleted_at`)
- `PATCH` for updates (partial)
- Pagination: `?page=1&page_size=20`

**Standard Error Response**:
```json
{
  "detail": "Error message here"
}
```

---

## Endpoint Inventory

### 1. Datasets `/datasets`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/datasets` | List datasets (paginated) |
| `POST` | `/datasets` | Create dataset |
| `GET` | `/datasets/{uuid}` | Get dataset |
| `PATCH` | `/datasets/{uuid}` | Update dataset |
| `DELETE` | `/datasets/{uuid}` | Soft delete dataset |

**Query params for GET list**: `page`, `page_size`, `source_type`, `entity_type`, `search`

---

### 2. Dataset Entries `/datasets/{uuid}/entries`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/datasets/{uuid}/entries` | List entries (paginated) |
| `POST` | `/datasets/{uuid}/entries` | Create entries (bulk) |
| `GET` | `/datasets/{uuid}/entries/{uuid}` | Get entry |
| `PATCH` | `/datasets/{uuid}/entries/{uuid}` | Update entry |
| `DELETE` | `/datasets/{uuid}/entries/{uuid}` | Soft delete entry |

**Query params for GET list**: `page`, `page_size`, `search`

**Bulk create**: POST accepts array of entries, all-or-nothing transaction.

---

### 3. Entry Properties `/entries/{uuid}/properties` (READ-ONLY)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/entries/{uuid}/properties` | List properties for entry |

*Create/Update/Delete deferred - properties come from imports.*

---

### 4. Property Definitions `/properties`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/properties` | List definitions (paginated) |
| `POST` | `/properties` | Create definition |
| `GET` | `/properties/{uuid}` | Get definition |
| `PATCH` | `/properties/{uuid}` | Update definition |
| `DELETE` | `/properties/{uuid}` | Soft delete definition |

**Query params for GET list**: `page`, `page_size`, `data_type`, `wikidata_only`

---

### 5. Projects `/projects`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects` | List projects (paginated) |
| `POST` | `/projects` | Create project |
| `GET` | `/projects/{uuid}` | Get project with stats |
| `PATCH` | `/projects/{uuid}` | Update project |
| `DELETE` | `/projects/{uuid}` | Soft delete project |

**Query params for GET list**: `page`, `page_size`, `status`, `dataset_uuid`

---

### 6. Project Workflow `/projects/{uuid}/...`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/projects/{uuid}/start` | Create tasks + activate project |
| `POST` | `/projects/{uuid}/rerun` | Reprocess selected tasks |
| `GET` | `/projects/{uuid}/stats` | Detailed statistics |
| `GET` | `/projects/{uuid}/export` | Download results (CSV/JSON) |
| `GET` | `/projects/{uuid}/approved-matches` | List approved matches |

#### `POST /projects/{uuid}/start`

Creates tasks for dataset entries and transitions project to active.

**Request**:
```json
{
  "entry_uuids": ["..."],        // Optional: specific entries (null = all)
  "search_strategies": ["..."]   // Optional: override config
}
```

**Response (202)**:
```json
{
  "message": "Project started",
  "tasks_created": 150,
  "project_status": "active"
}
```

#### `POST /projects/{uuid}/rerun`

Reset specific tasks for reprocessing.

**Request**:
```json
{
  "criteria": "failed",          // "failed" | "no_candidates" | "no_accepted"
  "task_uuids": ["..."]          // Optional: specific tasks
}
```

**Response (202)**:
```json
{
  "tasks_reset": 25
}
```

#### `GET /projects/{uuid}/stats`

Computed on-the-fly.

**Response**:
```json
{
  "total_tasks": 500,
  "by_status": {
    "new": 10,
    "awaiting_review": 350,
    "reviewed": 100,
    "failed": 5
  },
  "candidates": {
    "total": 1200,
    "accepted": 100,
    "rejected": 50
  },
  "avg_score": 75.5,
  "progress_percent": 22.0
}
```

#### `GET /projects/{uuid}/export`

**Query params**: `format` (csv|json), `status` (optional)

**Response**: File download

#### `GET /projects/{uuid}/approved-matches`

**Response**:
```json
{
  "matches": [
    {
      "task_uuid": "...",
      "entry_external_id": "ep-12345",
      "entry_display_name": "Wayne Gretzky",
      "wikidata_id": "Q5879",
      "score": 95
    }
  ],
  "total": 100
}
```

---

### 7. Tasks `/projects/{uuid}/tasks` + `/tasks/{uuid}`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects/{uuid}/tasks` | List tasks (paginated) |
| `POST` | `/projects/{uuid}/tasks` | Create task manually |
| `GET` | `/projects/{uuid}/tasks/{uuid}` | Get task |
| `GET` | `/tasks/{uuid}` | **Alias**: Get task by UUID alone |
| `PATCH` | `/projects/{uuid}/tasks/{uuid}` | Update task |
| `DELETE` | `/projects/{uuid}/tasks/{uuid}` | Soft delete task |
| `POST` | `/projects/{uuid}/tasks/{uuid}/skip` | Skip task |

**Query params for GET list**: `page`, `page_size`, `status`, `has_candidates`, `has_accepted`, `min_score`, `sort`, `order`

**Status transition validation**: Enforced per state machine. Returns 400 for invalid transitions unless `?admin_override=true`.

---

### 8. Match Candidates `/tasks/{uuid}/candidates`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks/{uuid}/candidates` | List candidates (not paginated) |
| `POST` | `/tasks/{uuid}/candidates` | Create candidates (bulk) |
| `GET` | `/tasks/{uuid}/candidates/{uuid}` | Get candidate |
| `PATCH` | `/tasks/{uuid}/candidates/{uuid}` | Update candidate |
| `DELETE` | `/tasks/{uuid}/candidates/{uuid}` | Soft delete candidate |
| `POST` | `/tasks/{uuid}/candidates/{uuid}/accept` | Accept candidate |
| `POST` | `/tasks/{uuid}/candidates/{uuid}/reject` | Reject candidate |
| `PATCH` | `/tasks/{uuid}/candidates/bulk` | Bulk update candidates |

**Bulk create/update**: All-or-nothing transaction.

**Duplicate QIDs allowed**: Same Wikidata ID can appear multiple times (different sources).

#### `POST /tasks/{uuid}/candidates/{uuid}/accept`

Transitions candidate to `accepted`, task to `reviewed`, sets `accepted_wikidata_id` on task.

**Response**:
```json
{
  "task": { /* TaskRead */ },
  "candidate": { /* MatchCandidateRead */ }
}
```

#### `PATCH /tasks/{uuid}/candidates/bulk`

**Request**:
```json
{
  "candidate_uuids": ["...", "..."],
  "updates": {
    "status": "rejected"
  }
}
```

**Response**: `list[MatchCandidateRead]`

---

### 9. Audit Logs `/audit-logs` (READ-ONLY)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/audit-logs` | List logs (paginated) |
| `GET` | `/audit-logs/{uuid}` | Get single log |

**Query params**: `page`, `page_size`, `entity_type`, `entity_uuid`, `action`, `from_date`, `to_date`

*Logs are created automatically by services*.

---

### 10. Wikidata Search `/wikidata/search` (STUB)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/wikidata/search` | Search Wikidata (mock) |

**Query params**: `query` (required), `type`, `limit`

**Response** (stub):
```json
{
  "results": [
    {
      "qid": "Q5879",
      "label": "Johann Wolfgang von Goethe",
      "description": "German writer",
      "aliases": ["Goethe"]
    }
  ]
}
```

*Returns hardcoded mock data for now. Real integration in Phase 6.*

---

## Deferred Features

Not implemented in Phase 5:

| Feature | Reason |
|---------|--------|
| Authentication | User decision (Q1) |
| File import (`/entries/import`) | User decision (Q13) |
| Entry property CRUD | Only GET needed (Q14) |
| Auto-acceptance | User decision (Q4) |
| Live Wikidata API | Stub only (Q5) |

---

## State Machine Enforcement

### Task Status Transitions

Valid transitions (enforced unless `?admin_override=true`):

```
new → queued_for_processing → processing → {failed, no_candidates_found, awaiting_review}
failed → queued_for_processing (retry)
awaiting_review → {reviewed, skipped, auto_confirmed}
no_candidates_found → skipped
```

### Candidate Status Transitions

```
suggested → {accepted, rejected}
```

*Once accepted/rejected, cannot change (except admin override).*

---

## Audit Log Strategy

Per Q7 (Combination):

| Action | Logged By |
|--------|-----------|
| Entity CRUD | Service layer (explicit) |
| Status changes | Service layer (explicit) |
| Accept/reject | Service layer (explicit) |
| Bulk operations | Service layer (per-item) |

---

## Questions for Clarification

> [!NOTE]
> A few refinement questions based on the first iteration:

### RQ1: Project Status on Start

When `POST /projects/{uuid}/start` is called, what should be the resulting status?

**Options**:
- A) `active` (ready for processing)
- B) `pending_search` (waiting for search job)
- C) `processing` (immediately start searching)

**Your Answer:**
B
---

### RQ2: Task Creation Strategy on Start

For `POST /projects/{uuid}/start` with no `entry_uuids`:

**Options**:
- A) Create tasks for ALL entries in dataset (could be thousands)
- B) Require explicit `entry_uuids` or `all_entries: true` flag
- C) Create tasks for first N entries, with pagination/continuation

**Your Answer:**
B
---

### RQ3: Export Format Details

For `GET /projects/{uuid}/export`:

**Options**:
- A) Implement CSV and JSON now
- B) Implement only JSON for now (simpler)
- C) Implement CSV only (more common for data export)

**Your Answer:**
B
---

### RQ4: Audit Log Granularity

For bulk operations, should we create:

**Options**:
- A) One audit log per bulk operation (e.g., "bulk_create_entries", count: 50)
- B) One audit log per item (50 separate logs)
- C) One summary log + one per-item only on errors

**Your Answer:**
B, but add context from A
---

### RQ5: Optional Candidate Details on Task List

When listing tasks (`GET /projects/{uuid}/tasks`), should we include:

**Options**:
- A) No candidate info (separate call to get candidates)
- B) Include top candidate only (highest score)
- C) Include candidate count + top candidate
- D) Full candidates array (could be large)

**Your Answer:**
A, but when we have some accepted candidate, then add the uuid of it
---

### RQ6: Entry Details in Task Response

When getting a task, should we include the full dataset entry details?

**Options**:
- A) No - only `dataset_entry_uuid`, client fetches separately
- B) Include `display_name` and `external_url` denormalized
- C) Include full entry object nested

**Your Answer:**
C
---

## Files to Create

```
backend/app/
├── api/v1/
│   ├── __init__.py       # Router aggregation
│   ├── datasets.py       # 5 endpoints
│   ├── entries.py        # 5 + 1 (properties GET)
│   ├── properties.py     # 5 endpoints
│   ├── projects.py       # 5 + 5 workflow
│   ├── tasks.py          # 6 + 1 skip + 1 alias
│   ├── candidates.py     # 5 + 3 shortcuts + 1 bulk
│   ├── audit_logs.py     # 2 endpoints
│   └── wikidata.py       # 1 stub
├── services/
│   ├── __init__.py
│   ├── base.py           # BaseService with common CRUD
│   ├── dataset_service.py
│   ├── entry_service.py
│   ├── property_service.py
│   ├── project_service.py
│   ├── task_service.py
│   ├── candidate_service.py
│   └── audit_service.py
```

**Total new endpoints**: ~45
**Total new files**: ~17

---

*End of API Specification v2*
