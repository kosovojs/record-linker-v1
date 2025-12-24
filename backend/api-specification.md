# API Specification v1

This document describes the API endpoints for the Record Linker backend, intended for frontend developers.

**Base URL:** `/api/v1`

---

## 1. Example Usage

### Workflow: Creating a Dataset and starting a Project

**Step 1: Create a Dataset**
`POST /datasets`
```json
{
  "name": "Berlin Landmarks",
  "slug": "berlin-landmarks",
  "source_type": "web_scrape",
  "entity_type": "building"
}
```
**Response (201 Created):**
```json
{
  "uuid": "440e8400-e29b-41d4-a716-446655440000",
  "name": "Berlin Landmarks",
  "slug": "berlin-landmarks",
  "description": null,
  "source_url": null,
  "source_type": "web_scrape",
  "entity_type": "building",
  "entry_count": 0,
  "last_synced_at": null,
  "extra_data": {},
  "created_at": "2024-12-24T15:00:00Z",
  "updated_at": "2024-12-24T15:00:00Z"
}
```

**Step 2: Start a Project**
`POST /projects/{uuid}/start`
```json
{
  "all_entries": true
}
```
**Response (202 Accepted):**
```json
{
  "message": "Project started",
  "tasks_created": 150,
  "project_status": "pending_search"
}
```

---

## 2. API Endpoints

### Datasets
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/datasets` | List datasets (paginated). Returns `PaginatedResponse[DatasetRead]`. |
| `POST` | `/datasets` | Create a dataset. Body: `DatasetCreate`. Returns `DatasetRead`. |
| `GET` | `/datasets/{uuid}` | Get dataset. Returns `DatasetRead`. |
| `PATCH` | `/datasets/{uuid}` | Update dataset. Body: `DatasetUpdate`. Returns `DatasetRead`. |
| `DELETE` | `/datasets/{uuid}` | Soft delete dataset. Returns `204 No Content`. |

### Dataset Entries
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/datasets/{dataset_uuid}/entries` | List entries. Returns `PaginatedResponse[DatasetEntryRead]`. |
| `POST` | `/datasets/{dataset_uuid}/entries` | Bulk create. Body: `list[DatasetEntryCreate]`. Returns `list[DatasetEntryRead]`. |
| `GET` | `/datasets/{dataset_uuid}/entries/{uuid}` | Get entry. Returns `DatasetEntryRead`. |
| `PATCH` | `/datasets/{dataset_uuid}/entries/{uuid}` | Update entry. Body: `DatasetEntryUpdate`. Returns `DatasetEntryRead`. |

### Projects
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/projects` | List projects. Returns `PaginatedResponse[ProjectRead]`. |
| `POST` | `/projects` | Create project. Body: `ProjectCreate`. Returns `ProjectRead`. |
| `GET` | `/projects/{uuid}` | Get project with stats. Returns `ProjectRead`. |
| `POST` | `/projects/{uuid}/start` | Start project. Body: `ProjectStartRequest`. Returns `ProjectStartResponse`. |
| `GET` | `/projects/{uuid}/stats` | Live stats. Returns `ProjectStatsResponse`. |
| `GET` | `/projects/{uuid}/approved-matches` | List matches. Returns `ApprovedMatchesResponse`. |

### Tasks
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/projects/{project_uuid}/tasks` | List project tasks. Returns `PaginatedResponse[TaskRead]`. |
| `GET` | `/tasks/{uuid}` | Get task by UUID. Returns `TaskRead`. |
| `POST` | `/projects/{project_uuid}/tasks/{uuid}/skip` | Skip task. Returns `TaskRead`. |

### Candidates
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/tasks/{task_uuid}/candidates` | List candidates. Returns `list[MatchCandidateRead]`. |
| `POST` | `/tasks/{task_uuid}/candidates/{uuid}/accept` | Accept match. Returns `AcceptRejectResponse`. |
| `POST` | `/tasks/{task_uuid}/candidates/{uuid}/reject` | Reject match. Returns `MatchCandidateRead`. |

---

## 3. Data Models

### Common
#### `PaginatedResponse[T]`
- `items`: `list[T]` - List of results for the current page.
- `total`: `int` - Total number of items available.
- `page`: `int` - Current page number.
- `page_size`: `int` - Items per page.
- `has_more`: `bool` - True if there are more pages.

### Datasets
#### `DatasetRead`
- `uuid`: `UUID` - Unique public identifier.
- `name`: `str` - Human-readable name.
- `slug`: `str` - URL-friendly identifier.
- `description`: `str | null` - Full description.
- `source_url`: `str | null` - Link to external data source.
- `source_type`: `str` - Enum: `web_scrape`, `csv`, `wikidata`.
- `entity_type`: `str` - Type of records (e.g., `person`, `city`).
- `entry_count`: `int` - Number of entries in this dataset.
- `created_at`: `datetime` - UTC ISO 8601 creation timestamp.

#### `DatasetCreate`
- `name` (required), `slug` (required), `entity_type` (required), `description`, `source_url`, `source_type`, `extra_data`.

### Projects
#### `ProjectRead`
- `uuid`: `UUID` - Unique identifier.
- `dataset_uuid`: `UUID` - Associated dataset.
- `name`: `str` - Project name.
- `description`: `str | null` - Description.
- `status`: `str` - Enum: `draft`, `active`, `completed`, `failed`.
- `task_count`: `int` - Total tasks.
- `tasks_completed`: `int` - Reviewed tasks.
- `tasks_with_candidates`: `int` - Tasks where search found results.
- `config`: `dict` - Matching configuration (rules, weights).

#### `ProjectStatsResponse`
- `total_tasks`: `int` - Total project tasks.
- `by_status`: `dict[str, int]` - Count per status (`new`, `pending`, `reviewed`, `failed`).
- `candidates`: `dict[str, int]` - Stats about candidates (`total`, `avg_per_task`).
- `progress_percent`: `float` - Overall completion percentage.

### Tasks
#### `TaskRead`
- `uuid`: `UUID` - Unique identifier.
- `project_uuid`: `UUID` - Parent project.
- `dataset_entry_uuid`: `UUID` - The data record being matched.
- `status`: `str` - Enum: `pending`, `reviewed`, `failed`, `skipped`.
- `accepted_wikidata_id`: `str | null` - The QID if a match was accepted.
- `candidate_count`: `int` - Candidates found for this record.
- `highest_score`: `int | null` - Best match score (0-100).
- `notes`: `str | null` - Reviewer comments.

### Candidates
#### `MatchCandidateRead`
- `uuid`: `UUID` - Unique identifier.
- `task_uuid`: `UUID` - Parent task.
- `wikidata_id`: `str` - The QID of the Wikidata entity.
- `status`: `str` - Enum: `new`, `accepted`, `rejected`.
- `score`: `int` - Overall match score (0-100).
- `source`: `str` - Enum: `search`, `manual`, `heuristic`.
- `score_breakdown`: `dict | null` - Detailed scores per property comparison.
- `matched_properties`: `dict | null` - Specific property values that matched.
- `tags`: `list[str]` - Custom labels.

---

## 4. Error Responses

The API uses standard HTTP status codes:
- `400 Bad Request`: Validation errors or invalid state transitions.
- `404 Not Found`: Entity with requested UUID does not exist.
- `409 Conflict`: Business logic conflict (e.g., slug already exists).
- `500 Internal Server Error`: Unexpected system failure.

**Standard Error Body:**
```json
{
  "detail": "Detailed error message describing the problem."
}
```
