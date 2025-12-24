# API Usage Guide

This guide walks through the typical happy path workflow for the Record Linker API.

**Base URL:** `http://localhost:8000/api/v1` (adjust to your local environment)

---

## 1. Preparing Data

### Create a Dataset
First, define a container for your data.

```bash
curl -X POST http://localhost:8000/api/v1/datasets -H "Content-Type: application/json" -d '{"name": "Berlin Museums", "slug": "berlin-museums", "source_type": "web_scrape", "entity_type": "museum"}'
```

**Note:** Save the `uuid` from the response (e.g., `440e8400-e29b-41d4-a716-446655440000`).

### Add Entries to the Dataset
Import the individual records you want to reconcile.

```bash
curl -X POST http://localhost:8000/api/v1/datasets/440e8400-e29b-41d4-a716-446655440000/entries -H "Content-Type: application/json" -d '[{"external_id": "mus-001", "display_name": "Pergamon Museum", "description": "Famous museum on Museum Island"}, {"external_id": "mus-002", "display_name": "Altes Museum"}]'
```

---

## 2. Setup Matching Logic (Optional)

### Create Property Definitions
Define which properties should be used for comparison during matching.

```bash
curl -X POST http://localhost:8000/api/v1/properties -H "Content-Type: application/json" -d '{"name": "inception", "data_type": "time", "wikidata_id": "P571"}'
```

---

## 3. Reconciliation Workflow

### Create a Project
A project links a dataset to a reconciliation process.

```bash
curl -X POST http://localhost:8000/api/v1/projects -H "Content-Type: application/json" -d '{"name": "Berlin Museum Reconciliation", "dataset_uuid": "440e8400-e29b-41d4-a716-446655440000"}'
```

**Note:** Save the project `uuid` (e.g., `550e8400-e29b-41d4-a716-446655440000`).

### Start the Project
This triggers the creation of tasks for all entries in the dataset.

```bash
curl -X POST http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/start -H "Content-Type: application/json" -d '{"all_entries": true}'
```

### Check Project Stats
Monitor the progress of the automated search and matching.

```bash
curl -X GET http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/stats
```

---

## 4. Refining Results

### List Tasks
Find tasks that need review (e.g., those with pending status).

```bash
curl -X GET "http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/tasks?status=pending"
```

**Note:** Save a task `uuid` (e.g., `770e8400-e29b-41d4-a716-446655440000`).

### List Candidates for a Task
See the potential Wikidata matches found by the system.

```bash
curl -X GET http://localhost:8000/api/v1/tasks/770e8400-e29b-41d4-a716-446655440000/candidates
```

### Accept a Candidate
Confirm a candidate as the correct match.

```bash
curl -X POST http://localhost:8000/api/v1/tasks/770e8400-e29b-41d4-a716-446655440000/candidates/880e8400-e29b-41d4-a716-446655440000/accept -H "Content-Type: application/json" -d '{}'
```

### Skip a Task
If you can't decide or want to handle it later.

```bash
curl -X POST http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/tasks/770e8400-e29b-41d4-a716-446655440000/skip -H "Content-Type: application/json" -d '{}'
```

---

## 5. Finalizing

### Get Approved Matches
Download the final results of your reconciliation effort.

```bash
curl -X GET http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/approved-matches
```

### Create Audit Log View
Check what actions were performed on a specific project.

```bash
curl -X GET "http://localhost:8000/api/v1/audit-logs?entity_type=project&entity_uuid=550e8400-e29b-41d4-a716-446655440000"
```
