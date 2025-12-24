# API Specification v1

This document is the absolute reference for the Record Linker API. It contains every endpoint (with descriptions), request/response model, and data type required for frontend development.

**Base URL:** `/api/v1`

---

## 1. Flow Examples

### Workflow A: Data Onboarding
1. **Create Dataset**: `POST /datasets`
   - Request: `{"name": "Berlin Museums", "slug": "berlin", "entity_type": "museum"}`
   - Response: `{"uuid": "...", "name": "Berlin Museums", ...}`
2. **Bulk Add Entries**: `POST /datasets/{uuid}/entries`
   - Request: `[{"external_id": "m1", "display_name": "Pergamon"}, {"external_id": "m2", "display_name": "Altes"}]`
   - Response: `[{"uuid": "...", "external_id": "m1", ...}, ...]`

### Workflow B: Reconciliation
1. **Create Project**: `POST /projects`
   - Request: `{"name": "Project 1", "dataset_uuid": "..."}`
   - Response: `{"uuid": "...", "status": "draft", ...}`
2. **Start Project**: `POST /projects/{uuid}/start`
   - Request: `{"all_entries": true}`
   - Response: `{"message": "Project started", "tasks_created": 2, "project_status": "pending_search"}`
3. **Accept Candidate**: `POST /tasks/{t_uuid}/candidates/{c_uuid}/accept`
   - Response:
     ```json
     {
       "task": {
         "uuid": "t_uuid",
         "status": "reviewed",
         "accepted_wikidata_id": "Q123",
         "candidate_count": 5,
         "highest_score": 95,
         ...
       },
       "candidate": {
         "uuid": "c_uuid",
         "status": "accepted",
         "score": 95,
         "wikidata_id": "Q123",
         "source": "automated_search",
         ...
       }
     }
     ```

---

## 2. API Endpoints

### Datasets
Manage collections of entities to be matched.

| Method | Path | Request | Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/datasets` | - | `Paginated[DatasetRead]` | List datasets with filters (name, slug, type). |
| `POST` | `/datasets` | `DatasetCreate` | `DatasetRead` | Create a new dataset. Slug must be unique. |
| `GET` | `/datasets/{uuid}` | - | `DatasetRead` | Retrieve detailed metadata for a specific dataset. |
| `PATCH` | `/datasets/{uuid}` | `DatasetUpdate` | `DatasetRead` | Update dataset fields. Soft-validation on unique slug. |
| `DELETE` | `/datasets/{uuid}` | - | `204 No Content` | Soft delete the dataset and its related entries. |

### Dataset Entries
Individual records within a dataset. Nested under `/datasets/{dataset_uuid}`.

| Method | Path | Request | Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/entries` | - | `Paginated[EntryRead]` | List entries for a dataset. Supports search by name. |
| `POST` | `/entries` | `list[EntryCreate]` | `list[EntryRead]` | Bulk import entries into a dataset. |
| `GET` | `/entries/{uuid}` | - | `EntryRead` | Get a single entry's full data including raw source. |
| `PATCH` | `/entries/{uuid}` | `EntryUpdate` | `EntryRead` | Update entry display name or raw/extra data. |
| `DELETE` | `/entries/{uuid}` | - | `204 No Content` | Soft delete an individual record. |

### Projects
Reconciliation projects that link datasets to Wikidata.

| Method | Path | Request | Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/projects` | - | `Paginated[ProjectRead]` | List reconciliation projects. |
| `POST` | `/projects` | `ProjectCreate` | `ProjectRead` | Create a project for a specific dataset. |
| `GET` | `/projects/{uuid}` | - | `ProjectRead` | Get project metadata and summary progress. |
| `PATCH` | `/projects/{uuid}` | `ProjectUpdate` | `ProjectRead` | Update project name, description or config. |
| `DELETE` | `/projects/{uuid}` | - | `204 No Content` | Soft delete project and its tasks. |
| `POST` | `/projects/{uuid}/start` | `StartRequest` | `StartResponse` | Initialize tasks for entries and start automation. |
| `POST` | `/projects/{uuid}/rerun` | `RerunRequest` | `RerunResponse` | Reset subsets of tasks to re-trigger automation. |
| `GET` | `/projects/{uuid}/stats` | - | `StatsResponse` | Complex stats computed dynamically across all tasks. |
| `GET` | `/projects/{uuid}/approved-matches` | - | `MatchesResponse` | Result set of all tasks with an accepted candidate. |

### Tasks
Individual matching units (one per entry in a project).

| Method | Path | Request | Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/projects/{p_uuid}/tasks` | - | `Paginated[TaskRead]` | List tasks with filters for status, score, or candidates. |
| `GET` | `/tasks/{uuid}` | - | `TaskRead` | Direct access to a task by its UUID. |
| `POST` | `/projects/{p_uuid}/tasks/{uuid}/skip` | - | `TaskRead` | Mark a task as skipped to move past it in review. |

### Candidates
Potential matches discovered for a task. Nested under `/tasks/{task_uuid}`.

| Method | Path | Request | Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/candidates` | - | `list[CandidateRead]` | List all potential Wikidata matches for the task. |
| `POST` | `/candidates` | `BulkCandCreate` | `list[CandidateRead]` | Manually add specific Wikidata IDs as candidates. |
| `GET` | `/candidates/{uuid}` | - | `CandidateRead` | Get details on a candidate's score breakdown. |
| `PATCH` | `/candidates/{uuid}` | `CandUpdate` | `CandidateRead` | Update candidate notes or tags. |
| `PATCH` | `/candidates/bulk` | `BulkUpdateReq` | `list[CandidateRead]` | Update many candidates at once (e.g. tag as AI). |
| `POST` | `/candidates/{uuid}/accept` | - | `AcceptResponse` | CONFIRM this match. Updates task to reviewed/accepted. |
| `POST` | `/candidates/{uuid}/reject` | - | `CandidateRead` | EXPLICITLY REJECT this match. |

### Properties
Configuration for property-based comparison.

| Method | Path | Request | Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/properties` | - | `Paginated[PropRead]` | List property definitions used for matching rules. |
| `POST` | `/properties` | `PropCreate` | `PropRead` | Define a new property for comparison (e.g. P569). |
| `GET` | `/properties/{uuid}` | - | `PropRead` | Get full property metadata including validation regex. |
| `PATCH` | `/properties/{uuid}` | `PropUpdate` | `PropRead` | Update property metadata or display order. |
| `DELETE` | `/properties/{uuid}` | - | `204 No Content` | Delete a property definition. |

---

## 3. Data Models

### Common Reponses
#### `PaginatedResponse[T]`
- `items`: `list[T]` - Data list for page.
- `total`: `int` - Total items in database.
- `page`: `int` - Current page.
- `page_size`: `int` - Items per page.
- `has_more`: `bool` - Next page exists.

#### `ErrorResponse`
- `detail`: `str | list[ErrorDetail]`

#### `ErrorDetail`
- `loc`: `list[str]` - Field path (e.g. `["body", "slug"]`).
- `msg`: `str` - Error message.
- `type`: `str` - Error category.

### Datasets
#### `DatasetRead`
- `uuid`: `UUID`
- `name`: `str`
- `slug`: `str`
- `description`: `str | null`
- `source_url`: `str | null`
- `source_type`: `DatasetSourceType`
- `entity_type`: `str` - Expected record type (e.g. `human`).
- `entry_count`: `int` - Cached count of related entries.
- `last_synced_at`: `datetime | null`
- `extra_data`: `dict`
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `DatasetCreate`
- `name`: `str` (required)
- `slug`: `str` (required, unique, snake_case)
- `entity_type`: `str` (required, e.g. `museum`)
- `description`: `str | null`
- `source_url`: `str | null`
- `source_type`: `DatasetSourceType`
- `extra_data`: `dict | null`

#### `DatasetUpdate`
(All fields optional): `name`, `slug`, `description`, `source_url`, `source_type`, `entity_type`, `extra_data`.

### Dataset Entries
#### `DatasetEntryRead`
- `uuid`: `UUID`
- `dataset_uuid`: `UUID | null`
- `external_id`: `str` - Original ID from source.
- `external_url`: `str | null` - Link to source.
- `display_name`: `str | null` - Label for search/UI.
- `raw_data`: `dict | null` - Full record from source.
- `extra_data`: `dict` - Computed metadata.
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `DatasetEntryCreate`
- `external_id`: `str` (required)
- `display_name`: `str | null`
- `external_url`: `str | null`
- `dataset_uuid`: `UUID` (required)
- `raw_data`: `dict | null`
- `extra_data`: `dict | null`

### Projects
#### `ProjectRead`
- `uuid`: `UUID`
- `dataset_uuid`: `UUID | null`
- `name`: `str`
- `description`: `str | null`
- `status`: `ProjectStatus`
- `owner_uuid`: `UUID | null`
- `task_count`: `int`
- `tasks_completed`: `int`
- `tasks_with_candidates`: `int`
- `config`: `dict` - Comparison logic weights and rules.
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `ProjectCreate`
- `name`: `str` (required)
- `dataset_uuid`: `UUID` (required)
- `description`: `str | null`
- `config`: `dict | null`

### Project Workflow
#### `ProjectStartRequest`
- `entry_uuids`: `list[UUID] | null` - List of entries to process.
- `all_entries`: `bool` - If true, ignores `entry_uuids`.

#### `ProjectStartResponse`
- `message`: `str` - Status message.
- `tasks_created`: `int` - Number of tasks initialized.
- `project_status`: `str` - New status of the project.

#### `ProjectRerunRequest`
- `criteria`: `str | null` - Enum: `failed`, `no_candidates`, `no_accepted`.
- `task_uuids`: `list[UUID] | null` - Specific tasks to reset.

#### `ProjectStatsResponse`
- `total_tasks`: `int`
- `by_status`: `dict[str, int]` - Count by machine status.
- `candidates`: `dict[str, int]` - `total` and `avg_per_task`.
- `avg_score`: `float | null` - Avg score of best candidates.
- `progress_percent`: `float` - Math: `completed / total`.

#### `ApprovedMatchesResponse`
- `matches`: `list[ApprovedMatch]`
- `total`: `int`

#### `ApprovedMatch`
- `task_uuid`: `str`
- `entry_external_id`: `str`
- `entry_display_name`: `str | null`
- `wikidata_id`: `str`
- `score`: `int`

### Tasks
#### `TaskRead`
- `uuid`: `UUID`
- `project_uuid`: `UUID`
- `dataset_entry_uuid`: `UUID`
- `status`: `TaskStatus`
- `notes`: `str | null`
- `accepted_wikidata_id`: `str | null` - The chosen QID.
- `candidate_count`: `int`
- `highest_score`: `int | null`
- `processing_started_at`: `datetime | null`
- `processing_finished_at`: `datetime | null`
- `reviewer_uuid`: `UUID | null`
- `reviewed_at`: `datetime | null`
- `extra_data`: `dict`
- `created_at`: `datetime`
- `updated_at`: `datetime`

### Candidates
#### `MatchCandidateRead`
- `uuid`: `UUID`
- `task_uuid`: `UUID`
- `wikidata_id`: `str` - Target QID.
- `score`: `int` - Final match probability (0-100).
- `source`: `CandidateSource`
- `status`: `CandidateStatus`
- `score_breakdown`: `dict | null` - Scores for name, date, etc.
- `matched_properties`: `dict | null` - Values used for comparison.
- `notes`: `str | null`
- `tags`: `list[str]`
- `reviewer_uuid`: `UUID | null`
- `reviewed_at`: `datetime | null`
- `extra_data`: `dict`
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `AcceptRejectResponse`
- `task`: `TaskRead`
- `candidate`: `MatchCandidateRead`

#### `BulkCandidateCreate`
- `candidates`: `list[MatchCandidateCreate]`

#### `BulkCandidateUpdateRequest`
- `candidate_uuids`: `list[UUID]`
- `updates`: `MatchCandidateUpdate` (score, status, notes, tags, extra_data)

### Properties
#### `PropertyDefinitionRead`
- `uuid`: `UUID`
- `name`: `str` - Code-key (e.g. `birth_date`).
- `display_name`: `str` - Visible label.
- `description`: `str | null`
- `data_type_hint`: `PropertyDataType`
- `is_multivalued`: `bool`
- `is_searchable`: `bool`
- `is_display_field`: `bool`
- `display_order`: `int`
- `wikidata_property`: `str | null`
- `validation_regex`: `str | null`
- `created_at`: `datetime`
- `updated_at`: `datetime`

---

## 4. Enums

### `DatasetSourceType`
`web_scrape`, `api`, `file_import`, `manual`

### `ProjectStatus`
`draft`, `active`, `pending_search`, `search_in_progress`, `search_completed`, `pending_processing`, `processing`, `processing_failed`, `review_ready`, `completed`, `archived`

### `TaskStatus`
`new`, `queued_for_processing`, `processing`, `failed`, `no_candidates_found`, `awaiting_review`, `reviewed`, `auto_confirmed`, `skipped`, `knowledge_based`

### `CandidateStatus`
`suggested`, `accepted`, `rejected`

### `CandidateSource`
`automated_search`, `manual`, `file_import`, `ai_suggestion`, `knowledge_base`

### `PropertyDataType`
`text`, `date`, `number`, `url`, `email`, `identifier`
