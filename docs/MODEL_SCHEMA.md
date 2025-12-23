# Record Linker - Model Schema

> **Version**: 1.0 (Draft)
> **Last Updated**: 2025-12-23

This document defines the data model for the Record Linker system. It serves as the specification for implementing database models and API contracts.

---

## Table of Contents
1. [Core Entities](#core-entities)
2. [External Data Layer](#external-data-layer)
3. [Reconciliation Layer](#reconciliation-layer)
4. [User & Audit Layer](#user--audit-layer)
5. [Common Patterns](#common-patterns)
6. [Indexes & Constraints](#indexes--constraints)

---

## Common Patterns

All entities follow these conventions:

### Base Fields (Present on ALL tables)
```
id              : BIGINT, PRIMARY KEY, AUTO INCREMENT
                  Internal ID, NEVER exposed via API

uuid            : UUID, UNIQUE, NOT NULL, DEFAULT gen_random_uuid()
                  Public identifier, used in all API responses

created_at      : TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT NOW()
updated_at      : TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT NOW()
                  Auto-updated on any modification

deleted_at      : TIMESTAMP WITH TIME ZONE, NULLABLE
                  Soft delete marker (NULL = active, set = deleted)
```

### Naming Conventions
- Tables: `snake_case`, plural (e.g., `datasets`, `match_candidates`)
- Columns: `snake_case`
- Foreign keys: `{related_table_singular}_id` (e.g., `dataset_id`)
- Indexes: `idx_{table}_{columns}`
- Unique constraints: `uq_{table}_{columns}`

---

## Core Entities

### 1. User

Represents a system user who can own projects and perform reviews.

```yaml
Table: users

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  email:
    type: VARCHAR(255)
    nullable: false
    unique: true
    description: User's email address (login identifier)

  display_name:
    type: VARCHAR(255)
    nullable: false
    description: Human-readable name for display

  password_hash:
    type: VARCHAR(255)
    nullable: true
    description: Hashed password (null if SSO-only)

  role:
    type: VARCHAR(50)
    nullable: false
    default: 'user'
    enum: [admin, user, viewer]
    description: |
      - admin: Full access, can manage users
      - user: Can create/manage own projects
      - viewer: Read-only access

  is_active:
    type: BOOLEAN
    nullable: false
    default: true
    description: Whether user can log in

  last_login_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: Last successful login timestamp

  settings:
    type: JSONB
    nullable: false
    default: '{}'
    description: User preferences (UI settings, notifications, etc.)

Indexes:
  - idx_users_email (email) WHERE deleted_at IS NULL
  - idx_users_role (role)

Constraints:
  - uq_users_email: UNIQUE(email) WHERE deleted_at IS NULL
```

---

## External Data Layer

These entities represent data imported from external sources.

### 2. Dataset

Represents an external data source (e.g., EliteProspects players database).

```yaml
Table: datasets

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  name:
    type: VARCHAR(255)
    nullable: false
    description: Human-readable name (e.g., "EliteProspects - Players")

  slug:
    type: VARCHAR(100)
    nullable: false
    unique: true
    description: URL-friendly identifier (e.g., "eliteprospects-players")

  description:
    type: TEXT
    nullable: true
    description: Detailed description of the dataset

  source_url:
    type: VARCHAR(500)
    nullable: true
    description: URL to the external source website

  source_type:
    type: VARCHAR(50)
    nullable: false
    default: 'web_scrape'
    enum: [web_scrape, api, file_import, manual]
    description: How data was obtained

  entity_type:
    type: VARCHAR(100)
    nullable: false
    description: Type of entities (e.g., "person", "organization", "location")

  entry_count:
    type: INTEGER
    nullable: false
    default: 0
    description: Cached count of entries (denormalized for performance)

  last_synced_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: Last time data was synced from source

  metadata:
    type: JSONB
    nullable: false
    default: '{}'
    description: |
      Additional metadata about the dataset:
      - version: string
      - license: string
      - contact: string
      - custom_fields: object

Indexes:
  - idx_datasets_slug (slug) WHERE deleted_at IS NULL
  - idx_datasets_entity_type (entity_type)
  - idx_datasets_source_type (source_type)

Constraints:
  - uq_datasets_slug: UNIQUE(slug) WHERE deleted_at IS NULL
```

---

### 3. PropertyDefinition

Defines a property type that can be attached to dataset entries (EAV pattern).

```yaml
Table: property_definitions

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  name:
    type: VARCHAR(100)
    nullable: false
    unique: true
    description: Machine-readable name (e.g., "date_of_birth", "full_name")

  display_name:
    type: VARCHAR(255)
    nullable: false
    description: Human-readable label (e.g., "Date of Birth", "Full Name")

  description:
    type: TEXT
    nullable: true
    description: Explanation of what this property represents

  data_type_hint:
    type: VARCHAR(50)
    nullable: false
    default: 'text'
    enum: [text, date, number, url, email, identifier]
    description: |
      Hint for UI rendering and validation.
      Note: All values stored as TEXT in EAV table.
      - text: Free-form text
      - date: ISO 8601 date (YYYY-MM-DD)
      - number: Numeric value (stored as string)
      - url: Valid URL
      - email: Email address
      - identifier: External system ID

  is_multivalued:
    type: BOOLEAN
    nullable: false
    default: false
    description: Whether multiple values are allowed for this property

  is_searchable:
    type: BOOLEAN
    nullable: false
    default: true
    description: Whether this property should be indexed for search

  is_display_field:
    type: BOOLEAN
    nullable: false
    default: false
    description: Whether to show in summary views (name, title, etc.)

  display_order:
    type: INTEGER
    nullable: false
    default: 0
    description: Order for display in UI (lower = first)

  wikidata_property:
    type: VARCHAR(20)
    nullable: true
    description: |
      Corresponding Wikidata property ID (e.g., "P569" for DOB).
      Used for automated matching and comparison.

  validation_regex:
    type: VARCHAR(500)
    nullable: true
    description: Optional regex for value validation

Indexes:
  - idx_property_definitions_name (name) WHERE deleted_at IS NULL
  - idx_property_definitions_data_type (data_type_hint)
  - idx_property_definitions_wikidata (wikidata_property) WHERE wikidata_property IS NOT NULL

Constraints:
  - uq_property_definitions_name: UNIQUE(name) WHERE deleted_at IS NULL
```

---

### 4. DatasetEntry

An individual record from an external dataset (e.g., one person profile).

```yaml
Table: dataset_entries

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  dataset_id:
    type: BIGINT
    nullable: false
    references: datasets(id)
    description: Parent dataset

  external_id:
    type: VARCHAR(255)
    nullable: false
    description: ID from the external source (stable identifier)

  display_name:
    type: VARCHAR(500)
    nullable: true
    description: |
      Cached display name for UI (denormalized).
      Derived from properties like "full_name" or "title".

  external_url:
    type: VARCHAR(500)
    nullable: true
    description: Direct URL to this entry in the source system

  raw_data:
    type: JSONB
    nullable: true
    description: |
      Original raw data from source (for reference/debugging).
      Not used for matching - use properties instead.

  metadata:
    type: JSONB
    nullable: false
    default: '{}'
    description: |
      Additional metadata:
      - imported_at: timestamp
      - import_batch: string
      - quality_score: number

Indexes:
  - idx_dataset_entries_dataset (dataset_id) WHERE deleted_at IS NULL
  - idx_dataset_entries_external_id (dataset_id, external_id) WHERE deleted_at IS NULL
  - idx_dataset_entries_display_name (display_name) WHERE deleted_at IS NULL
  - idx_dataset_entries_raw_data (raw_data) USING GIN  -- For JSONB queries

Constraints:
  - uq_dataset_entries_external: UNIQUE(dataset_id, external_id) WHERE deleted_at IS NULL
  - fk_dataset_entries_dataset: FOREIGN KEY (dataset_id) REFERENCES datasets(id)
```

---

### 5. DatasetEntryProperty

Stores property values for dataset entries (EAV value table).

```yaml
Table: dataset_entry_properties

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  dataset_entry_id:
    type: BIGINT
    nullable: false
    references: dataset_entries(id)
    description: Parent entry

  property_definition_id:
    type: BIGINT
    nullable: false
    references: property_definitions(id)
    description: Property type being set

  value:
    type: TEXT
    nullable: false
    description: The property value (always stored as text)

  value_normalized:
    type: TEXT
    nullable: true
    description: |
      Normalized/cleaned version for matching:
      - Lowercase
      - Diacritics removed
      - Whitespace normalized

  confidence:
    type: SMALLINT
    nullable: true
    check: confidence >= 0 AND confidence <= 100
    description: |
      Confidence score for extracted values (0-100).
      NULL if not applicable (manually entered data).

  source:
    type: VARCHAR(50)
    nullable: false
    default: 'import'
    enum: [import, manual, derived, api]
    description: How this value was obtained

  ordinal:
    type: SMALLINT
    nullable: false
    default: 0
    description: |
      Order within multi-valued properties.
      0 = primary value, 1+ = additional values.
      For single-valued properties, always 0.

Indexes:
  - idx_dep_entry (dataset_entry_id) WHERE deleted_at IS NULL
  - idx_dep_property (property_definition_id) WHERE deleted_at IS NULL
  - idx_dep_entry_property (dataset_entry_id, property_definition_id) WHERE deleted_at IS NULL
  - idx_dep_value_normalized (value_normalized) WHERE deleted_at IS NULL AND value_normalized IS NOT NULL
  - idx_dep_value_fulltext USING GIN (to_tsvector('simple', value))  -- Full-text search

Constraints:
  - uq_dep_entry_property_ordinal: UNIQUE(dataset_entry_id, property_definition_id, ordinal) WHERE deleted_at IS NULL
  - fk_dep_entry: FOREIGN KEY (dataset_entry_id) REFERENCES dataset_entries(id)
  - fk_dep_property: FOREIGN KEY (property_definition_id) REFERENCES property_definitions(id)
```

---

## Reconciliation Layer

These entities manage the matching process.

### 6. Project

A reconciliation project for a dataset (top-level work unit).

```yaml
Table: projects

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  dataset_id:
    type: BIGINT
    nullable: false
    references: datasets(id)
    description: Dataset being reconciled

  owner_id:
    type: BIGINT
    nullable: false
    references: users(id)
    description: User who owns this project

  name:
    type: VARCHAR(255)
    nullable: false
    description: Project name (e.g., "EP Players - Batch 1 - Hockey")

  description:
    type: TEXT
    nullable: true
    description: Project description and notes

  status:
    type: VARCHAR(50)
    nullable: false
    default: 'draft'
    enum:
      - draft
      - active
      - pending_search
      - search_in_progress
      - search_completed
      - pending_processing
      - processing
      - processing_failed
      - review_ready
      - completed
      - archived
    description: Current project status

  # Denormalized counts for performance
  task_count:
    type: INTEGER
    nullable: false
    default: 0
    description: Total number of tasks

  tasks_completed:
    type: INTEGER
    nullable: false
    default: 0
    description: Number of tasks in terminal states

  tasks_with_candidates:
    type: INTEGER
    nullable: false
    default: 0
    description: Number of tasks with at least one candidate

  # Configuration
  config:
    type: JSONB
    nullable: false
    default: '{}'
    description: |
      Project configuration:
      - auto_accept_threshold: number (0-100, auto-accept candidates above this score)
      - search_strategies: string[] (which search methods to use)
      - matching_weights: object (property weights for scoring)
      - max_candidates_per_task: number

  started_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: When processing started

  completed_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: When project was marked completed

Indexes:
  - idx_projects_dataset (dataset_id) WHERE deleted_at IS NULL
  - idx_projects_owner (owner_id) WHERE deleted_at IS NULL
  - idx_projects_status (status) WHERE deleted_at IS NULL
  - idx_projects_created (created_at DESC) WHERE deleted_at IS NULL

Constraints:
  - fk_projects_dataset: FOREIGN KEY (dataset_id) REFERENCES datasets(id)
  - fk_projects_owner: FOREIGN KEY (owner_id) REFERENCES users(id)
```

---

### 7. Task

Links a project to a dataset entry (unit of work for matching).

```yaml
Table: tasks

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  project_id:
    type: BIGINT
    nullable: false
    references: projects(id)
    description: Parent project

  dataset_entry_id:
    type: BIGINT
    nullable: false
    references: dataset_entries(id)
    description: Entry to be matched

  status:
    type: VARCHAR(50)
    nullable: false
    default: 'new'
    enum:
      - new
      - queued_for_processing
      - processing
      - failed
      - no_candidates_found
      - awaiting_review
      - reviewed
      - auto_confirmed
      - skipped
      - knowledge_based
    description: Current task status

  # Accepted match (denormalized for quick access)
  accepted_candidate_id:
    type: BIGINT
    nullable: true
    references: match_candidates(id)
    description: |
      The accepted candidate (if any).
      Denormalized from match_candidates for quick filtering.

  accepted_wikidata_id:
    type: VARCHAR(20)
    nullable: true
    description: |
      Accepted Wikidata QID (e.g., "Q12345").
      Denormalized for quick access without joins.

  # Processing metadata
  candidate_count:
    type: INTEGER
    nullable: false
    default: 0
    description: Number of candidates found (denormalized)

  highest_score:
    type: SMALLINT
    nullable: true
    check: highest_score >= 0 AND highest_score <= 100
    description: Highest candidate score (for sorting/filtering)

  processing_started_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: When candidate search started

  processing_completed_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: When candidate search finished

  reviewed_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: When human review was completed

  reviewed_by_id:
    type: BIGINT
    nullable: true
    references: users(id)
    description: User who reviewed this task

  notes:
    type: TEXT
    nullable: true
    description: Reviewer notes

  error_message:
    type: TEXT
    nullable: true
    description: Error details if status is 'failed'

  metadata:
    type: JSONB
    nullable: false
    default: '{}'
    description: |
      Additional metadata:
      - search_queries: string[] (queries used for search)
      - processing_time_ms: number
      - retry_count: number

Indexes:
  - idx_tasks_project (project_id) WHERE deleted_at IS NULL
  - idx_tasks_entry (dataset_entry_id) WHERE deleted_at IS NULL
  - idx_tasks_project_status (project_id, status) WHERE deleted_at IS NULL
  - idx_tasks_status (status) WHERE deleted_at IS NULL
  - idx_tasks_accepted_wikidata (accepted_wikidata_id) WHERE deleted_at IS NULL AND accepted_wikidata_id IS NOT NULL
  - idx_tasks_highest_score (highest_score DESC NULLS LAST) WHERE deleted_at IS NULL
  - idx_tasks_reviewed_by (reviewed_by_id) WHERE deleted_at IS NULL AND reviewed_by_id IS NOT NULL

Constraints:
  - uq_tasks_project_entry: UNIQUE(project_id, dataset_entry_id) WHERE deleted_at IS NULL
  - fk_tasks_project: FOREIGN KEY (project_id) REFERENCES projects(id)
  - fk_tasks_entry: FOREIGN KEY (dataset_entry_id) REFERENCES dataset_entries(id)
  - fk_tasks_accepted: FOREIGN KEY (accepted_candidate_id) REFERENCES match_candidates(id)
  - fk_tasks_reviewer: FOREIGN KEY (reviewed_by_id) REFERENCES users(id)
```

---

### 8. MatchCandidate

A potential Wikidata match for a task.

```yaml
Table: match_candidates

Fields:
  # Base fields (id, uuid, created_at, updated_at, deleted_at)

  task_id:
    type: BIGINT
    nullable: false
    references: tasks(id)
    description: Parent task

  wikidata_id:
    type: VARCHAR(20)
    nullable: false
    description: |
      Wikidata item ID (e.g., "Q12345").
      Format: Q followed by digits.

  status:
    type: VARCHAR(50)
    nullable: false
    default: 'suggested'
    enum:
      - suggested
      - accepted
      - rejected
    description: Current candidate status

  score:
    type: SMALLINT
    nullable: false
    check: score >= 0 AND score <= 100
    description: Match confidence score (0-100, higher = better)

  source:
    type: VARCHAR(50)
    nullable: false
    enum:
      - automated_search
      - manual
      - file_import
      - ai_suggestion
      - knowledge_base
    description: How this candidate was found

  # Scoring breakdown
  score_breakdown:
    type: JSONB
    nullable: true
    description: |
      Detailed scoring by component:
      {
        "name_similarity": 85,
        "date_match": 100,
        "country_match": 80,
        "occupation_match": 70,
        ...
      }

  # Match evidence
  matched_properties:
    type: JSONB
    nullable: true
    description: |
      Properties that contributed to the match:
      {
        "P569": {"source": "1990-05-15", "wikidata": "1990-05-15", "match": true},
        "P27": {"source": "Canada", "wikidata": "Q16", "match": true},
        ...
      }

  # Tags for categorization
  tags:
    type: VARCHAR(50)[]
    nullable: false
    default: '{}'
    description: |
      User-defined tags for filtering/categorization:
      - "high_confidence"
      - "needs_verification"
      - "possible_duplicate"
      - etc.

  notes:
    type: TEXT
    nullable: true
    description: Free-text notes about this candidate

  reviewed_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: true
    description: When this candidate was reviewed

  reviewed_by_id:
    type: BIGINT
    nullable: true
    references: users(id)
    description: User who reviewed this candidate

  metadata:
    type: JSONB
    nullable: false
    default: '{}'
    description: |
      Additional metadata:
      - search_query: string (query that found this)
      - rank_in_results: number
      - api_response_time_ms: number

Indexes:
  - idx_mc_task (task_id) WHERE deleted_at IS NULL
  - idx_mc_task_status (task_id, status) WHERE deleted_at IS NULL
  - idx_mc_wikidata (wikidata_id) WHERE deleted_at IS NULL
  - idx_mc_status (status) WHERE deleted_at IS NULL
  - idx_mc_score (score DESC) WHERE deleted_at IS NULL
  - idx_mc_source (source) WHERE deleted_at IS NULL
  - idx_mc_tags USING GIN (tags) WHERE deleted_at IS NULL
  - idx_mc_reviewed_by (reviewed_by_id) WHERE deleted_at IS NULL AND reviewed_by_id IS NOT NULL

Constraints:
  - fk_mc_task: FOREIGN KEY (task_id) REFERENCES tasks(id)
  - fk_mc_reviewer: FOREIGN KEY (reviewed_by_id) REFERENCES users(id)

Notes:
  - Same wikidata_id CAN appear multiple times for same task (different sources)
  - No unique constraint on (task_id, wikidata_id) by design
```

---

## User & Audit Layer

### 9. AuditLog

Tracks all significant actions for compliance and debugging.

```yaml
Table: audit_logs

Fields:
  # Note: No soft delete for audit logs - they are permanent
  id:
    type: BIGINT
    primary_key: true
    auto_increment: true

  uuid:
    type: UUID
    nullable: false
    unique: true
    default: gen_random_uuid()

  created_at:
    type: TIMESTAMP WITH TIME ZONE
    nullable: false
    default: NOW()

  user_id:
    type: BIGINT
    nullable: true
    references: users(id)
    description: User who performed action (null for system actions)

  action:
    type: VARCHAR(100)
    nullable: false
    description: |
      Action type:
      - project.created, project.updated, project.status_changed
      - task.status_changed, task.reviewed
      - candidate.accepted, candidate.rejected
      - user.login, user.logout
      - etc.

  entity_type:
    type: VARCHAR(50)
    nullable: false
    description: Type of entity affected (project, task, candidate, user, etc.)

  entity_id:
    type: BIGINT
    nullable: true
    description: Internal ID of affected entity

  entity_uuid:
    type: UUID
    nullable: true
    description: Public UUID of affected entity

  old_value:
    type: JSONB
    nullable: true
    description: Previous state (for updates)

  new_value:
    type: JSONB
    nullable: true
    description: New state (for updates)

  context:
    type: JSONB
    nullable: false
    default: '{}'
    description: |
      Additional context:
      - ip_address: string
      - user_agent: string
      - request_id: string
      - batch_id: string (for bulk operations)

  description:
    type: TEXT
    nullable: true
    description: Human-readable description of the action

Indexes:
  - idx_audit_user (user_id)
  - idx_audit_action (action)
  - idx_audit_entity (entity_type, entity_id)
  - idx_audit_entity_uuid (entity_type, entity_uuid)
  - idx_audit_created (created_at DESC)

Notes:
  - Audit logs are NEVER deleted (no soft delete)
  - Consider partitioning by created_at for large deployments
  - May need retention policy for GDPR compliance
```

---

## State Transitions

### Project State Machine

```
┌─────────┐
│  draft  │
└────┬────┘
     │ activate
     ▼
┌─────────┐     start_search      ┌─────────────────┐
│ active  │ ──────────────────▶   │ pending_search  │
└─────────┘                       └────────┬────────┘
     │                                     │
     │ archive                             ▼
     │                            ┌────────────────────┐
     │                            │ search_in_progress │
     │                            └────────┬───────────┘
     │                                     │
     │                                     ▼
     │                            ┌──────────────────┐
     │                            │ search_completed │
     │                            └────────┬─────────┘
     │                                     │
     │                                     ▼
     │                            ┌────────────────────┐
     │                            │ pending_processing │
     │                            └────────┬───────────┘
     │                                     │
     │                           ┌─────────┴─────────┐
     │                           ▼                   ▼
     │                    ┌────────────┐    ┌────────────────────┐
     │                    │ processing │    │ processing_failed  │
     │                    └─────┬──────┘    └────────────────────┘
     │                          │                    │
     │                          ▼                    │ retry
     │                    ┌──────────────┐           │
     │                    │ review_ready │ ◀─────────┘
     │                    └──────┬───────┘
     │                           │ all_reviewed
     │                           ▼
     │                    ┌───────────┐
     └──────────────────▶ │ completed │
                          └─────┬─────┘
                                │
                                ▼
                          ┌──────────┐
                          │ archived │
                          └──────────┘
```

### Task State Machine

```
┌─────┐
│ new │
└──┬──┘
   │ queue
   ▼
┌───────────────────────┐
│ queued_for_processing │
└───────────┬───────────┘
            │ process
            ▼
      ┌────────────┐
      │ processing │
      └─────┬──────┘
            │
    ┌───────┼───────────────┐
    │       │               │
    ▼       ▼               ▼
┌────────┐ ┌──────────────────┐ ┌─────────────────────┐
│ failed │ │ no_candidates_   │ │ awaiting_review     │
└────┬───┘ │ found            │ └──────────┬──────────┘
     │     └─────────┬────────┘            │
     │               │                     │
     │ retry         │ skip       ┌────────┼─────────┐
     │               ▼            │        │         │
     │          ┌─────────┐       ▼        ▼         ▼
     └────────▶ │ skipped │ ┌──────────┐ ┌────────┐ ┌────────────────┐
                └─────────┘ │ reviewed │ │skipped │ │ auto_confirmed │
                            └──────────┘ └────────┘ └────────────────┘
                                  ▲
                                  │
                            ┌─────┴───────────┐
                            │ knowledge_based │
                            └─────────────────┘
```

### Candidate State Machine

```
┌───────────┐
│ suggested │
└─────┬─────┘
      │
      ├──────────────────┐
      │                  │
      ▼                  ▼
┌──────────┐       ┌──────────┐
│ accepted │       │ rejected │
└──────────┘       └──────────┘
```

---

## Database Views (Recommended)

### v_project_stats
```sql
-- Aggregated project statistics for dashboard
SELECT
  p.uuid,
  p.name,
  p.status,
  COUNT(t.id) as total_tasks,
  COUNT(t.id) FILTER (WHERE t.status = 'reviewed') as reviewed_tasks,
  COUNT(t.id) FILTER (WHERE t.status = 'awaiting_review') as pending_tasks,
  COUNT(t.id) FILTER (WHERE t.accepted_wikidata_id IS NOT NULL) as matched_tasks,
  AVG(t.highest_score) FILTER (WHERE t.highest_score IS NOT NULL) as avg_score
FROM projects p
LEFT JOIN tasks t ON t.project_id = p.id AND t.deleted_at IS NULL
WHERE p.deleted_at IS NULL
GROUP BY p.id;
```

### v_task_details
```sql
-- Task with entry and candidate info for review UI
SELECT
  t.uuid as task_uuid,
  t.status as task_status,
  de.display_name as entry_name,
  de.external_url,
  t.candidate_count,
  t.highest_score,
  t.accepted_wikidata_id,
  p.uuid as project_uuid,
  p.name as project_name
FROM tasks t
JOIN dataset_entries de ON de.id = t.dataset_entry_id
JOIN projects p ON p.id = t.project_id
WHERE t.deleted_at IS NULL;
```

---

## API Resource Mapping

| Entity | API Endpoint | Public ID |
|--------|--------------|-----------|
| User | `/api/users/{uuid}` | uuid |
| Dataset | `/api/datasets/{uuid}` | uuid (or slug) |
| PropertyDefinition | `/api/properties/{uuid}` | uuid (or name) |
| DatasetEntry | `/api/datasets/{dataset_uuid}/entries/{uuid}` | uuid |
| Project | `/api/projects/{uuid}` | uuid |
| Task | `/api/projects/{project_uuid}/tasks/{uuid}` | uuid |
| MatchCandidate | `/api/tasks/{task_uuid}/candidates/{uuid}` | uuid |

---

## Migration Notes

1. **Order of creation**:
   - users → datasets → property_definitions → dataset_entries → dataset_entry_properties → projects → tasks → match_candidates → audit_logs

2. **UUID generation**: Use `gen_random_uuid()` (PostgreSQL 13+) or `uuid_generate_v4()` (with pgcrypto)

3. **Timezone**: All timestamps should be `TIMESTAMP WITH TIME ZONE`

4. **Initial data**:
   - Create default admin user
   - Create common property definitions (name, date_of_birth, country, etc.)
