# API Specification v1

This document is the absolute reference for the Record Linker API. It contains every endpoint, request/response model, and data type required for frontend development.

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
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/datasets` | - | `PaginatedResponse[DatasetRead]` |
| `POST` | `/datasets` | `DatasetCreate` | `DatasetRead` |
| `GET` | `/datasets/{uuid}` | - | `DatasetRead` |
| `PATCH` | `/datasets/{uuid}` | `DatasetUpdate` | `DatasetRead` |
| `DELETE` | `/datasets/{uuid}` | - | `204 No Content` |

### Dataset Entries (Nested under /datasets/{dataset_uuid})
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/entries` | - | `PaginatedResponse[DatasetEntryRead]` |
| `POST` | `/entries` | `list[DatasetEntryCreate]` | `list[DatasetEntryRead]` |
| `GET` | `/entries/{uuid}` | - | `DatasetEntryRead` |
| `PATCH` | `/entries/{uuid}` | `DatasetEntryUpdate` | `DatasetEntryRead` |
| `DELETE` | `/entries/{uuid}` | - | `204 No Content` |

### Projects
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/projects` | - | `PaginatedResponse[ProjectRead]` |
| `POST` | `/projects` | `ProjectCreate` | `ProjectRead` |
| `GET` | `/projects/{uuid}` | - | `ProjectRead` |
| `PATCH` | `/projects/{uuid}` | `ProjectUpdate` | `ProjectRead` |
| `DELETE` | `/projects/{uuid}` | - | `204 No Content` |
| `POST` | `/projects/{uuid}/start` | `ProjectStartRequest` | `ProjectStartResponse` |
| `POST` | `/projects/{uuid}/rerun` | `ProjectRerunRequest` | `ProjectRerunResponse` |
| `GET` | `/projects/{uuid}/stats` | - | `ProjectStatsResponse` |
| `GET` | `/projects/{uuid}/approved-matches` | - | `ApprovedMatchesResponse` |

### Tasks
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/projects/{project_uuid}/tasks` | - | `PaginatedResponse[TaskRead]` |
| `GET` | `/tasks/{uuid}` | - | `TaskRead` |
| `POST` | `/projects/{project_uuid}/tasks/{uuid}/skip` | - | `TaskRead` |

### Candidates (Nested under /tasks/{task_uuid})
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/candidates` | - | `list[MatchCandidateRead]` |
| `POST` | `/candidates` | `BulkCandidateCreate` | `list[MatchCandidateRead]` |
| `GET` | `/candidates/{uuid}` | - | `MatchCandidateRead` |
| `PATCH` | `/candidates/{uuid}` | `MatchCandidateUpdate` | `MatchCandidateRead` |
| `PATCH` | `/candidates/bulk` | `BulkCandidateUpdateRequest` | `list[MatchCandidateRead]` |
| `POST` | `/candidates/{uuid}/accept` | - | `AcceptRejectResponse` |
| `POST` | `/candidates/{uuid}/reject` | - | `MatchCandidateRead` |

### Properties
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/properties` | - | `PaginatedResponse[PropertyDefinitionRead]` |
| `POST` | `/properties` | `PropertyDefinitionCreate` | `PropertyDefinitionRead` |
| `GET` | `/properties/{uuid}` | - | `PropertyDefinitionRead` |
| `PATCH` | `/properties/{uuid}` | `PropertyDefinitionUpdate` | `PropertyDefinitionRead` |
| `DELETE` | `/properties/{uuid}` | - | `204 No Content` |

### Wikidata
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/wikidata/search` | - | `WikidataSearchResponse` |
| `GET` | `/wikidata/entity/{qid}` | - | `JSON Object` |

### Audit Logs
| Method | Path | Request Body | Response Model |
| :--- | :--- | :--- | :--- |
| `GET` | `/audit-logs` | - | `PaginatedResponse[AuditLogRead]` |
| `GET` | `/audit-logs/{uuid}` | - | `AuditLogRead` |

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
- `loc`: `list[str]` - Field path.
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
- `entity_type`: `str`
- `entry_count`: `int`
- `last_synced_at`: `datetime | null`
- `extra_data`: `dict`
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `DatasetCreate`
- `name`: `str` (required, max 100)
- `slug`: `str` (required, max 50)
- `entity_type`: `str` (required, max 50)
- `description`: `str | null`
- `source_url`: `str | null`
- `source_type`: `DatasetSourceType` (default: `web_scrape`)
- `extra_data`: `dict | null`

#### `DatasetUpdate`
(All fields optional): `name`, `slug`, `description`, `source_url`, `source_type`, `entity_type`, `extra_data`.

### Dataset Entries
#### `DatasetEntryRead`
- `uuid`: `UUID`
- `dataset_uuid`: `UUID | null`
- `external_id`: `str`
- `external_url`: `str | null`
- `display_name`: `str | null`
- `raw_data`: `dict | null`
- `extra_data`: `dict`
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `DatasetEntryCreate`
- `external_id`: `str` (required)
- `display_name`: `str | null`
- `external_url`: `str | null`
- `dataset_uuid`: `UUID` (required)
- `raw_data`: `dict | null`
- `extra_data`: `dict | null`

#### `DatasetEntryUpdate`
(All fields optional): `external_id`, `external_url`, `display_name`, `raw_data`, `extra_data`.

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
- `config`: `dict` (e.g., weights: `{"name": 0.8, "date": 0.2}`)
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `ProjectCreate`
- `name`: `str` (required)
- `dataset_uuid`: `UUID` (required)
- `description`: `str | null`
- `config`: `dict | null`

#### `ProjectUpdate`
(All fields optional): `name`, `description`, `status`, `config`.

### Project Workflow
#### `ProjectStartRequest`
- `entry_uuids`: `list[UUID] | null`
- `all_entries`: `bool` (default: `false`)

#### `ProjectStartResponse`
- `message`: `str`
- `tasks_created`: `int`
- `project_status`: `str`

#### `ProjectRerunRequest`
- `criteria`: `str | null` (Options: `failed`, `no_candidates`, `no_accepted`)
- `task_uuids`: `list[UUID] | null`

#### `ProjectRerunResponse`
- `tasks_reset`: `int`

#### `ProjectStatsResponse`
- `total_tasks`: `int`
- `by_status`: `dict[str, int]` (Keys: `new`, `processing`, `reviewed`, etc.)
- `candidates`: `dict[str, int]` (Keys: `total`, `avg_per_task`)
- `avg_score`: `float | null`
- `progress_percent`: `float`

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
- `accepted_wikidata_id`: `str | null`
- `candidate_count`: `int`
- `highest_score`: `int | null`
- `processing_started_at`: `datetime | null`
- `processing_finished_at`: `datetime | null`
- `reviewer_uuid`: `UUID | null`
- `reviewed_at`: `datetime | null`
- `extra_data`: `dict`
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `TaskCreate`
- `project_uuid`: `UUID`
- `dataset_entry_uuid`: `UUID`
- `status`: `TaskStatus` (default: `new`)
- `extra_data`: `dict | null`

#### `TaskUpdate`
(All fields optional): `status`, `notes`, `accepted_wikidata_id`, `extra_data`.

### Candidates
#### `MatchCandidateRead`
- `uuid`: `UUID`
- `task_uuid`: `UUID`
- `wikidata_id`: `str`
- `score`: `int` (0-100)
- `source`: `CandidateSource`
- `status`: `CandidateStatus`
- `score_breakdown`: `dict | null`
- `matched_properties`: `dict | null`
- `notes`: `str | null`
- `tags`: `list[str]`
- `reviewer_uuid`: `UUID | null`
- `reviewed_at`: `datetime | null`
- `extra_data`: `dict`
- `created_at`: `datetime`
- `updated_at`: `datetime`

#### `MatchCandidateCreate`
- `wikidata_id`: `str` (required)
- `score`: `int` (required)
- `source`: `CandidateSource` (default: `automated_search`)
- `score_breakdown`: `dict | null`
- `matched_properties`: `dict | null`
- `notes`: `str | null`
- `tags`: `list[str] | null`
- `extra_data`: `dict | null`

#### `MatchCandidateUpdate`
(All fields optional): `score`, `status`, `notes`, `tags`, `extra_data`.

#### `BulkCandidateCreate`
- `candidates`: `list[MatchCandidateCreate]` (min 1)

#### `BulkCandidateUpdateRequest`
- `candidate_uuids`: `list[UUID]` (min 1)
- `updates`: `MatchCandidateUpdate`

#### `AcceptRejectResponse`
- `task`: `TaskRead`
- `candidate`: `MatchCandidateRead`

### Properties
#### `PropertyDefinitionRead`
- `uuid`: `UUID`
- `name`: `str`
- `display_name`: `str`
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

#### `PropertyDefinitionCreate`
- `name`: `str` (required, snake_case)
- `display_name`: `str` (required)
- `description`: `str | null`
- `data_type_hint`: `PropertyDataType` (default: `text`)
- `is_multivalued`: `bool` (default: `false`)
- `is_searchable`: `bool` (default: `true`)
- `is_display_field`: `bool` (default: `false`)
- `display_order`: `int` (default: `0`)
- `wikidata_property`: `str | null` (Pattern: `P\d+`)
- `validation_regex`: `str | null`

#### `PropertyDefinitionUpdate`
(All fields optional): `name`, `display_name`, `description`, `data_type_hint`, `is_multivalued`, `is_searchable`, `is_display_field`, `display_order`, `wikidata_property`, `validation_regex`.

### Wikidata
#### `WikidataSearchResponse`
- `results`: `list[WikidataSearchResult]`

#### `WikidataSearchResult`
- `qid`: `str`
- `label`: `str`
- `description`: `str | null`
- `aliases`: `list[str]`

### Audit Logs
#### `AuditLogRead`
- `uuid`: `UUID`
- `user_uuid`: `UUID | null`
- `action`: `str` (e.g., `project.created`)
- `entity_type`: `str` (e.g., `project`, `task`)
- `entity_uuid`: `UUID | null`
- `old_value`: `dict | null`
- `new_value`: `dict | null`
- `context`: `dict` (request context)
- `description`: `str | null`
- `created_at`: `datetime`

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
