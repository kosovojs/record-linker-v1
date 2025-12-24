# API Specification v1

This document describes the API endpoints for the Record Linker backend.

**Base URL:** `/api/v1`

---

## Datasets

Endpoints for managing datasets (collections of entities to be matched).

### `GET /datasets`
List all datasets with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number.
- `page_size` (int, default: 20): Items per page.
- `source_type` (str, optional): Filter by source type (e.g., `wikidata`, `csv`, `web_scrape`).
- `entity_type` (str, optional): Filter by entity type (e.g., `human`, `city`).
- `search` (str, optional): Search in name or description.

**Response (200 OK):** `PaginatedResponse[DatasetRead]`

---

### `POST /datasets`
Create a new dataset.

**Request Body:** `DatasetCreate`
- `name` (str, required)
- `slug` (str, required): URL-friendly identifier.
- `description` (str, optional)
- `source_url` (str, optional)
- `source_type` (str, default: `web_scrape`)
- `entity_type` (str, required)
- `extra_data` (dict, optional)

**Response (201 Created):** `DatasetRead`

---

### `GET /datasets/{uuid}`
Get a single dataset by UUID.

**Path Parameters:**
- `uuid` (UUID): Dataset unique identifier.

**Response (200 OK):** `DatasetRead`

---

### `PATCH /datasets/{uuid}`
Update a dataset.

**Request Body:** `DatasetUpdate` (all fields optional)

**Response (200 OK):** `DatasetRead`

---

### `DELETE /datasets/{uuid}`
Soft delete a dataset.

**Response (204 No Content)**

---

## Dataset Entries

Individual records within a dataset.

### `GET /datasets/{dataset_uuid}/entries`
List entries for a specific dataset.

**Query Parameters:**
- `page`, `page_size`
- `search` (str, optional): Search in display names.

**Response (200 OK):** `PaginatedResponse[DatasetEntryRead]`

---

### `POST /datasets/{dataset_uuid}/entries`
Bulk create entries for a dataset.

**Request Body:** `list[DatasetEntryCreate]`
- `external_id` (str, required): ID from the source system.
- `display_name` (str, required)
- `description` (str, optional)
- `extra_data` (dict, optional)
- `raw_data` (dict, optional)

**Response (201 Created):** `list[DatasetEntryRead]`

---

### `GET /datasets/{dataset_uuid}/entries/{entry_uuid}`
Get a single entry.

**Response (200 OK):** `DatasetEntryRead`

---

### `PATCH /datasets/{dataset_uuid}/entries/{entry_uuid}`
Update an entry.

**Response (200 OK):** `DatasetEntryRead`

---

### `DELETE /datasets/{dataset_uuid}/entries/{entry_uuid}`
Soft delete an entry.

**Response (204 No Content)**

---

## Projects

Reconciliation projects that link datasets to Wikidata.

### `GET /projects`
List projects.

**Query Parameters:**
- `status` (str, optional): Filter by project status (`draft`, `active`, `completed`, `failed`).
- `dataset_uuid` (UUID, optional): Filter by dataset.

**Response (200 OK):** `PaginatedResponse[ProjectRead]`

---

### `POST /projects`
Create a project.

**Request Body:** `ProjectCreate`
- `name` (str, required)
- `description` (str, optional)
- `dataset_uuid` (UUID, required)
- `config` (dict, optional)

**Response (201 Created):** `ProjectRead`

---

### `POST /projects/{uuid}/start`
Start processing for a project.

**Request Body:** `ProjectStartRequest`
- `entry_uuids` (list[UUID], optional)
- `all_entries` (bool, default: false)

**Response (202 Accepted):** `ProjectStartResponse`

---

### `GET /projects/{uuid}/stats`
Get live project statistics.

**Response (200 OK):** `ProjectStatsResponse`

---

### `GET /projects/{uuid}/approved-matches`
List all approved matches for a project.

**Response (200 OK):** `ApprovedMatchesResponse`

---

## Tasks

Individual reconciliation tasks (one per entry).

### `GET /projects/{project_uuid}/tasks`
List tasks for a project with filtering.

**Query Parameters:**
- `status` (str, optional): Filter by status (`pending`, `failed`, `reviewed`, `skipped`).
- `has_candidates` (bool, optional)
- `has_accepted` (bool, optional)
- `min_score` (int, 0-100, optional)

**Response (200 OK):** `PaginatedResponse[TaskRead]`

---

### `GET /tasks/{uuid}`
Direct access to a task by its UUID.

**Response (200 OK):** `TaskRead`

---

### `POST /projects/{project_uuid}/tasks/{uuid}/skip`
Skip a task (mark as skipped).

**Response (200 OK):** `TaskRead`

---

## Candidates

Potential Wikidata matches for a task.

### `GET /tasks/{task_uuid}/candidates`
List all candidates for a task.

**Response (200 OK):** `list[MatchCandidateRead]`

---

### `POST /tasks/{task_uuid}/candidates/{uuid}/accept`
Accept a candidate as the correct match.

**Response (200 OK):** `AcceptRejectResponse`

---

### `POST /tasks/{task_uuid}/candidates/{uuid}/reject`
Explicitly reject a candidate.

**Response (200 OK):** `MatchCandidateRead`

---

## Property Definitions

Definitions for properties compared during matching.

### `GET /properties`
List property definitions.

**Query Parameters:**
- `data_type` (str, optional)
- `wikidata_only` (bool, default: false)

**Response (200 OK):** `PaginatedResponse[PropertyDefinitionRead]`

---

## Wikidata

Direct Wikidata integration.

### `GET /wikidata/search`
Search Wikidata entities.

**Query Parameters:**
- `query` (str, required)
- `type` (str, optional, e.g., `item`)
- `limit` (int, default: 10)
- `language` (str, default: `en`)

**Response (200 OK):** `WikidataSearchResponse`

---

### `GET /wikidata/entity/{qid}`
Get a specific Wikidata entity by QID (e.g., `Q42`).

**Response (200 OK):** `dict` (qid, label, description, aliases)

---

## Audit Logs

History of actions performed on entities.

### `GET /audit-logs`
List audit logs.

**Query Parameters:**
- `entity_type`, `entity_uuid`, `action`, `from_date`, `to_date`

**Response (200 OK):** `PaginatedResponse[AuditLogRead]`
