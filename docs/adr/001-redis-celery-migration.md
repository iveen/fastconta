# ADR 001: Replace BackgroundTasks with Redis + Celery

## Status
🟡 Proposed

## Context
Currently, FastAPI's built-in `BackgroundTasks` handles asynchronous jobs. This approach has several limitations:
- **No persistence**: Tasks are lost if the web server restarts.
- **No retry mechanism**: Failed tasks are silently dropped.
- **No horizontal scaling**: Workers are tied to the web server lifecycle.
- **No monitoring**: No visibility into task queues or failures.

With the projected growth of FastConta (more tenants, more invoices, more asset depreciation jobs), we need a robust, scalable async task system.

## Decision
We will replace `BackgroundTasks` with **Celery** using **Redis** as the message broker.

### Why Celery over alternatives?
| Alternative | Pros | Cons |
| :--- | :--- | :--- |
| **Celery + Redis** | Battle-tested, Flower for monitoring, built-in retries, multi-worker support | Slightly heavier setup |
| **RQ (Redis Queue)** | Simpler, lighter | Limited retry policies, less monitoring |
| **ARQ (Async Redis)** | Async-native | Smaller community, fewer integrations |
| **Dramatiq** | Fast | Less familiar to the team |

Celery wins due to its mature ecosystem, built-in retries, and excellent integration with Flower for real-time monitoring.

## Consequences
### Positive
- Tasks survive worker restarts.
- Failed tasks can be retried with exponential backoff.
- We can scale horizontally by running multiple Celery workers.
- We gain a monitoring dashboard (Flower).

### Negative
- Added infrastructure complexity (must run Redis + Celery worker in production).
- Developers must run Redis locally (or via Docker).
- Existing endpoints that rely on immediate background execution will need slight refactoring.

## Migration Plan (Phased)
1. **Phase 1 (Infrastructure)**: Add Redis to `docker-compose.yml`, add Celery dependencies, create `celery_app.py`.
2. **Phase 2 (Task Migration)**: Convert one job (e.g., email sending) to a Celery task while keeping the old system as a fallback.
3. **Phase 3 (Full Switch)**: Remove `BackgroundTasks` entirely and update all endpoint calls to Celery's `.delay()`.

## Related Links
- Issue: #123 (replace with your actual issue number once created)
- Branch: `feature/redis-celery-overhaul` 
## Related Links
- Issue: #42
- Branch: feature/redis-celery-overhaul
