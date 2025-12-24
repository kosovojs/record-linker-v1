# Background Processing Architecture (V3)

> **Status**: Final
> **Phase**: 6+ Implementation Guide
> **Scope**: Asynchronous Task Processing & Data Pipelines

## 1. Executive Summary

This architecture decouples the User-Facing API from high-latency operations (Wikidata syncing, bulk matching). It ensures the system remains **responsive** (returns `202 Accepted` < 50ms) regardless of the background workload size.

**Key Design Decisions:**
-   **At-Least-Once Delivery**: Jobs may be processed twice; logic must be idempotent.
-   **Resilience First**: External failures (API outages) are handled via backoff/retry, not crashes.
-   **Horizontal Scalability**: Workers are stateless and scalable independent of the API.

---

## 2. Architecture Overview

```mermaid
graph TD
    User -->|HTTP POST| API[API Server]

    subgraph "Producer Layer"
        API -->|1. Write Task (PENDING)| DB[(Database)]
        API -->|2. Enqueue Job| Broker[(Message Broker)]
    end

    subgraph "Consumer Layer"
        Worker[Worker Process] -->|3. Poll Job| Broker
        Worker -->|4. Fetch Context| DB
        Worker -->|5. External API| W[Wikidata]
        Worker -->|6. Save Result| DB
    end

    subgraph "Safety Nets"
        Cron[Sweeper Cron] -->|Repair Lost Tasks| DB
        Broker -->|Dead Letter| DLQ[DLQ]
    end
```

---

## 3. The Job Protocol

Jobs are **lightweight signals**. They carry *intent* and *references*, not heavy data.

### 3.1 Job Envelope Schema
```json
{
  "header": {
    "job_id": "c138...7f7a",
    "type": "entity.match",
    "version": "1.0",
    "correlation_id": "req_123abc",
    "created_at": "2024-12-24T12:00:00Z"
  },
  "context": {
    "user_id": 42,
    "user_role": "admin",
    "trace_id": "0af7..."
  },
  "payload": {
    "task_id": 1024,
    "project_id": 50
  }
}
```

### 3.2 Security & Context
-   **User Context**: Jobs inherit the permissions of the user who triggered them. The `context` block allows the worker to perform audit logging (`AuditLog.user_id`) correctly.
-   **System Jobs**: Automated jobs (Cron) use a special `system` context (`user_id=None`).

---

## 4. Core Workflows

### 4.1 Batch Processing (Fan-Out)
When a user starts a project with 10k items:
1.  **API**: Creates 10k `Task` rows (`status='PENDING'`).
2.  **API**: Enqueues 1 "ProjectCoordinator" job.
3.  **Coordinator Worker**:
    -   Reads 10k Task IDs.
    -   Chunks them (e.g., blocks of 100).
    -   Enqueues 100 "BatchMatch" jobs (each containing 100 task_ids).
    -   *Why?* Reduces Broker overhead compared to 10k individual messages.

### 4.2 Handling Race Conditions
**Golden Rule**: The Database is the Source of Truth. The Job is just a trigger.

```python
async def process_match(task_id):
    # 1. Verification
    task = await db.get(Task, task_id)
    if not task or task.status == 'CANCELLED':
        return ACK

    # 2. Execution
    try:
        matches = await wikidata_service.search(task.entry)

        # 3. Optimistic Write
        result = await db.execute(
            update(Task)
            .where(Task.id == task_id, Task.status == 'PENDING')
            .values(status='COMPLETED', result=matches)
        )
        if result.rowcount == 0:
            logger.warn("Task state changed mid-execution")

    except Exception:
        # Let the infrastructure handle retry policy
        raise
```

---

## 5. Resilience & Observability

### 5.1 The Sweeper (Safety Net)
A Cron process running every 10 minutes to find "Zombie Tasks":
`SELECT * FROM tasks WHERE status='PENDING' AND created_at < NOW() - INTERVAL '1 hour'`
-   **Action**: These tasks were likely committed to DB but the Broker crashed before enqueue. The Sweeper re-enqueues them.

### 5.2 Observability Metrics (SLIs)
| Metric | Definition | Importance |
|--------|------------|------------|
| `queue_age_sec` | Age of oldest message | Detects stuck consumers. |
| `jobs_failed_total` | Count of jobs moving to DLQ | Detects code bugs/poison pills. |
| `task_end_to_end_latency` | `finished_at - created_at` | User experience impact. |

---

## 6. Testing Strategy

Async systems are notoriously hard to test. We use a 3-layer approach.

### 6.1 Unit Tests (Logic)
-   **Scope**: `MatchingService`, `WikidataService`.
-   **Mock**: Everything (DB, Network).
-   **Goal**: Ensure business logic works given inputs.

### 6.2 Service Integration Tests (The Worker)
-   **Scope**: The `perform_job` function.
-   **Setup**: Spin up a real Test DB.
-   **Mock**: The *Broker* (call function directly) and *External API* (VCR/Mock).
-   **Goal**: Ensure the worker correctly reads DB, handles "Cancelled" state, and writes results.

### 6.3 End-to-End Tests (Architecture)
-   **Scope**: API -> Broker -> Worker.
-   **Implementation**:
    1.  Test Client POSTs to `/projects/{id}/start`.
    2.  Assert HTTP 202.
    3.  Assert `Task.status == 'PENDING'`.
    4.  *Manually trigger* the Worker function (simulating a consumed message).
    5.  Assert `Task.status == 'COMPLETED'`.
    -   *Note*: Avoid spinning up a real Broker container in CI if possible; use an in-memory broker emulator.

---

## 7. Implementation Guidelines

### Phase A: Interfaces
Define `JobDispatcher` protocol.
```python
class JobDispatcher(Protocol):
    async def enqueue(self, job: Job) -> None: ...
```

### Phase B: Infrastructure (Celery/Taskiq)
-   **Broker**: Redis (Simple, Fast).
-   **Backend**: None (We use our SQL DB for state).
-   **Serialization**: JSON only (No Pickle).

### Phase C: Deployment
-   **Workers**: Deploy as separate Deployment in K8s.
-   **Scaling**: HPA based on `queue_depth`.
