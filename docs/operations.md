# Phase 20 Operational Runbook

This runbook describes day-to-day operations, monitoring metrics, worker daemon management, outbox processing, and database disaster recovery procedures.

---

## 1. Metrics & Observability

The platform aggregates Prometheus-compatible metrics in-memory via `MetricsCollector` and exports OpenTelemetry traces to OTLP endpoints (`OTEL_EXPORTER_OTLP_ENDPOINT`).

### Key Metrics Monitored

* **`api_total_requests`**: Total HTTP request volume grouped by route and status code.
* **`api_total_errors`**: Total 4xx / 5xx HTTP response counts.
* **`task_executions`**: Task execution count grouped by status (`pending`, `completed`, `failed`).
* **`agent_runs`**: Agent executions grouped by model name and completion state.
* **`worker_jobs_processed`**: Total background jobs completed by daemon worker instances.
* **`outbox_backlog_depth`**: Count of pending transactional outbox events waiting to be dispatched.

---

## 2. Background Worker Daemon Management

Background processing is isolated from the HTTP server using `ProductionWorker` (`src/infrastructure/worker.py`).

### Worker Lifecycle State Transitions

```
[ STARTING ] ──> [ READY ] ──> [ RUNNING ] ──> [ DRAINING ] ──> [ STOPPED ]
```

* **Graceful Drain**: When `SIGTERM` or `SIGINT` is sent to the worker container, `WorkerLifecycleManager` transitions the worker state to `DRAINING`.
* **In-Flight Job Protection**: In-flight jobs are allowed to complete up to `DRAIN_TIMEOUT_SECONDS` (default: 30s) before database sessions are closed and the process terminates cleanly (`STOPPED`).

---

## 3. Transactional Outbox Engine

Event publishing is decoupled from API transactions using the **Transactional Outbox Pattern**:

1. Domain transactions write outbox events into the `outbox_messages` table within the same ACID database transaction.
2. `TransactionalOutboxProcessor` polls pending outbox messages, dispatches them through `EventDispatcher` or custom message brokers, and marks status as `PROCESSED`.
3. **Failure Isolation**: Unhandled dispatch errors trigger retry counters with exponential backoff before being marked as `FAILED` to prevent queue head-of-line blocking.

---

## 4. Automated Database Backup & Disaster Recovery

### Automated Database Backup Script

Run the automated backup script to create a schema & data snapshot with SHA-256 integrity verification:

```bash
python -m scripts.backup_database
```

Output:
```
DATABASE BACKUP COMPLETED SUCCESSFULLY
  Backup Key:  backups/db_backup_20260916_201021.json
  Storage Ref: scratch/artifact_storage/backups_db_backup_20260916_201021.json
  Checksum:    ed3f861dced93a0b5df521cb2072a225ca6c7d7aa399b67650c1525c8ce5ffa8
  Tables:      101
```

### Database Restoration & Verification Script

To restore a database snapshot from Object Storage with checksum validation:

```bash
python -m scripts.restore_database backups/db_backup_20260916_201021.json
```

1. Downloads the backup JSON snapshot from Object Storage / Local storage.
2. Re-computes and verifies the SHA-256 checksum against the stored checksum header.
3. Restores schema structure and records.
4. Executes readiness health checks to confirm database operational integrity.
