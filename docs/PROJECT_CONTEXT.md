# Record Linker - Project Context

> **Purpose**: This document captures all context needed to resume work on this project in a new session.

## Project Overview

**Record Linker** is a data reconciliation system that connects entity profiles from external data sources (like sports databases, Olympic records, etc.) to Wikidata items.

### Core Use Case
- External sources (e.g., EliteProspects, Olympedia) contain structured profiles of people
- Each profile has metadata: names, DOB, biography, achievements, etc.
- Goal: Match these profiles to corresponding Wikidata entities (QIDs)
- Support iterative, targeted reconciliation runs with human review

---

## Key Design Decisions (from Q&A)

### Data Sources & Datasets
| Question | Decision |
|----------|----------|
| Dataset cardinality | One source typically = one dataset, but can have multiple |
| Entry identifiers | Assume all sources have stable unique IDs |
| Property definitions | **Global** (shared across all datasets) |
| Property data types | Text-based (EAV model), support multiple values per property |

### Projects & Tasks
| Question | Decision |
|----------|----------|
| Project scope | Single dataset per project |
| Task selection | Provide entry IDs; default = all entries |
| Task uniqueness | Same entry can appear in multiple projects |
| Task ordering | No explicit ordering required |

### Matching & Candidates
| Question | Decision |
|----------|----------|
| Candidate sources | Automated search, manual, file import, AI suggestion |
| Multiple accepted | Primarily one, but design for flexibility |
| Score range | **0-100** (integer) |
| Deduplication | Keep separate (same QID from different sources = separate candidates) |
| Wikidata storage | **QID reference only** (no cached data) |

### Workflow & State
| Question | Decision |
|----------|----------|
| State transitions | Implement strict valid transitions |
| Audit trail | **Yes** - track all status changes with user and timestamp |
| Bulk operations | Support bulk status updates |

### Technical
| Question | Decision |
|----------|----------|
| Multi-user | Yes, with user ownership/permissions |
| User tracking | Via audit trail table |
| Soft delete | **Yes** - all records use soft delete |
| Public identifiers | **UUIDs only** (never expose internal IDs) |

---

## Entity Relationships (High-Level)

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│  Property   │     │    Dataset      │────▶│   DatasetEntry      │
│ Definition  │     │  (ext source)   │     │ (people profiles)   │
└─────────────┘     └─────────────────┘     └─────────────────────┘
       │                                              │
       │                                              │
       ▼                                              ▼
┌─────────────────────┐                    ┌─────────────────────┐
│ DatasetEntryProperty│◀───────────────────│       Task          │
│ (EAV values)        │                    │ (project ↔ entry)   │
└─────────────────────┘                    └─────────────────────┘
                                                      │
                           ┌──────────────────────────┤
                           │                          │
                           ▼                          ▼
                    ┌─────────────┐          ┌─────────────────┐
                    │   Project   │          │ MatchCandidate  │
                    │             │          │ (Wikidata QID)  │
                    └─────────────┘          └─────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    User     │
                    └─────────────┘
```

---

## Status Enums

### Project Statuses
| Status | Description |
|--------|-------------|
| `draft` | Initial state, project being configured |
| `active` | Project is active and being worked on |
| `pending_search` | Waiting for candidate search to begin |
| `search_in_progress` | Automated search running |
| `search_completed` | Search finished, results available |
| `pending_processing` | Waiting for processing pipeline |
| `processing` | Background processing active |
| `processing_failed` | Processing encountered errors |
| `review_ready` | All tasks ready for human review |
| `completed` | All tasks reviewed/resolved |
| `archived` | Project archived (soft-archived, still visible) |

### Task Statuses
| Status | Description |
|--------|-------------|
| `new` | Just created, no processing yet |
| `queued_for_processing` | In queue for candidate search |
| `processing` | Currently being processed |
| `failed` | Processing failed |
| `no_candidates_found` | Search completed, no matches |
| `awaiting_review` | Has candidates, needs human review |
| `reviewed` | Human has reviewed and made decision |
| `auto_confirmed` | System auto-accepted a high-confidence match |
| `skipped` | User explicitly skipped this task |
| `knowledge_based` | Resolved via knowledge base / rules |

### Candidate Statuses
| Status | Description |
|--------|-------------|
| `suggested` | Candidate proposed, awaiting review |
| `accepted` | User accepted this candidate |
| `rejected` | User rejected this candidate |

---

## Candidate Sources (Enum)
- `automated_search` - System search algorithms
- `manual` - User manually added
- `file_import` - Imported from file
- `ai_suggestion` - AI/ML model suggestion
- `knowledge_base` - Rule-based matching

---

## Next Steps

1. ✅ Complete model schema design
2. ⏳ User review and approval
3. 🔜 Implement database migrations
4. 🔜 Implement backend API
5. 🔜 Implement frontend UI

---

## File Structure (Planned)

```
record-linker/
├── docs/
│   ├── PROJECT_CONTEXT.md    # This file
│   └── MODEL_SCHEMA.md       # Detailed schema
├── backend/
│   ├── models/               # SQLAlchemy models
│   ├── api/                  # API routes
│   └── services/             # Business logic
└── frontend/
    └── ...
```
