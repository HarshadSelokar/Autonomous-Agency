# Autonomous Agency — Comprehensive Repository Audit
**Generated:** November 2026  
**Auditor:** Principal Software & Security Architect  
**Repository:** `agency`  
**Classification:** Foundational Architecture & Audit Report  

---

## 1. Executive Summary

This audit evaluates the **Autonomous Agency** codebase against the requirements of the **Master Project Directive** to transform the repository into a production-grade, persistent, remotely accessible multi-agent AI operating system.

The repository currently exhibits a **dual-architecture profile**:
1. **The Modern Software Studio**: A focused, reactive, multi-agent development engine ([`src/application/dev_team_service.py`](file:///d:/agency/src/application/dev_team_service.py)) where a Manager, Developer(s), QA Engineer, and Code Reviewer collaborate using Git worktrees, dual execution engines (`LoopEngine` and headless `AgyEngine`), and a live 2D isometric pixel-office frontend.
2. **The Enterprise / Company OS Layer**: A 22-phase organizational simulation platform ([`src/domain/`](file:///d:/agency/src/domain/), [`src/application/`](file:///d:/agency/src/application/), [`migrations/`](file:///d:/agency/migrations/)) featuring departments, workforce planning, dynamic swarms, strategic intelligence, GTM, ventures, and resilience management.

### Key Metrics Reconciled
* **Collected Tests**: **852 tests** across `tests/unit`, `tests/integration`, `tests/security`, `tests/failure_injection`, and `tests/concurrency` (resolving outdated references in `progress.md` claiming 527 tests).
* **Database Migrations**: **40 Alembic migrations** (`001_create_agents.py` through `040_office_timestamps_with_timezone.py`), resolving documentation claiming only 20 migrations.
* **Core Strengths**: Clean domain-driven design models, strict dataclass validation, asynchronous architecture, Git worktree isolation for developer concurrency, and comprehensive test coverage.
* **Primary Deficiencies**:
  * Studio tasks execute inside in-memory FastAPI server tasks rather than a durable, distributed worker queue.
  * Command execution relies on software allowlists rather than OS-level containerization/sandboxing.
  * Disaster recovery snapshots are kept in memory rather than durable object storage.
  * Audit hash chains have race conditions and in-memory cache drift under concurrent writes.
  * Tool approval grants lack parameter hashes, TTLs, and workspace bindings.

---

## 2. Directory Structure & Inventory

```
agency/
├── alembic.ini                    # Alembic migration configuration
├── benchmarks/                    # Benchmark harness evaluation suite
├── config/                        # Declarative Agent & Employee YAMLs
│   ├── agents/researcher.yaml
│   └── employees/alice_researcher.yaml
├── docker-compose.yml             # Dev/staging infrastructure (PG, Redis, MinIO, API, Worker)
├── Dockerfile                     # Multi-stage production API image
├── Dockerfile.worker              # Background worker image
├── docs/                          # Architecture, deployment, and phase documentation
├── frontend/                      # React 18 + Vite + TypeScript frontend
│   ├── src/
│   │   ├── Root.tsx               # Root router switching between Studio and Legacy OS
│   │   ├── studio/                # Modern Studio UI (Office Canvas, Kanban, Event Feed)
│   │   ├── components/            # Legacy Enterprise Dashboards (20+ dashboards)
│   │   └── services/              # API and WebSocket clients
├── migrations/                    # 40 Alembic migrations (001 - 040)
│   └── versions/
├── pyproject.toml                 # Build config & Python dependencies
├── scripts/                       # Operational scripts, benchmark runners, db restores
├── src/
│   ├── api/                       # FastAPI routes, schemas, and auth middleware
│   │   ├── middleware/            # Tenant, security, resilience context
│   │   └── routes/                # 40+ route handlers (Studio, Agents, Swarms, etc.)
│   ├── application/               # Application services, orchestrators, engines
│   │   ├── agent_loop.py          # Multi-step ReAct execution engine
│   │   ├── dev_team_service.py    # Software Studio Orchestrator
│   │   ├── studio_service.py      # Studio background task manager
│   │   ├── audit_governance_v2.py # Audit trail & hash-chain verifier
│   │   └── disaster_recovery_engine.py # DR snapshot engine
│   ├── domain/                    # Pure domain models, enums, exceptions
│   │   ├── agent.py               # Agent entity & state machine
│   │   ├── dev_project.py         # Studio project, ticket, activity domain
│   │   ├── employee.py            # Organizational employee entity
│   │   ├── tool.py                # Tool & approval domain
│   │   └── governance.py          # Policies & compliance
│   └── infrastructure/            # Implementations (SQLAlchemy, Redis, MinIO, CLI)
│       ├── coding/                # Git workspace, CommandRunner, LoopEngine, AgyEngine
│       ├── models/                # SQLAlchemy ORM models (001-040)
│       └── repositories/          # Database repositories
└── tests/                         # 852 unit, integration, security, & concurrency tests
```

---

## 3. Comprehensive Feature Classification

Every major feature across the platform is classified below according to the seven standard criteria:
1. **Implemented and verified**: Working end-to-end with automated test verification.
2. **Implemented but not adequately tested**: Functional in code, but lacks edge-case or integration test suites.
3. **Partially implemented**: Core logic exists, but key hooks or persistence paths are incomplete.
4. **Mocked or simulated**: Simulated in-memory or uses dummy responses.
5. **Documented but not implemented**: Mentioned in docs but absent in source code.
6. **Broken or inconsistent**: Contains bugs, race conditions, or architecture mismatches.
7. **Missing**: Required by the target vision but not yet started.

| Component / Subsystem | Current File Location | Status Classification | Assessment & Notes |
| :--- | :--- | :--- | :--- |
| **Studio Multi-Agent Dev Team** | [`src/application/dev_team_service.py`](file:///d:/agency/src/application/dev_team_service.py) | **Implemented and verified** | Manager, Developers, QA, Reviewer orchestration working with worktrees. |
| **Agent ReAct Loop** | [`src/application/agent_loop.py`](file:///d:/agency/src/application/agent_loop.py) | **Implemented and verified** | Multi-turn think-act-observe cycle, tool dispatch, JSON repair. |
| **Dual Engine (Loop vs Agy)** | [`src/infrastructure/coding/loop_engine.py`](file:///d:/agency/src/infrastructure/coding/loop_engine.py), [`agy_engine.py`](file:///d:/agency/src/infrastructure/coding/agy_engine.py) | **Implemented and verified** | Supports direct API models and headless `agy` CLI processes. |
| **Git Worktree Manager** | [`src/infrastructure/coding/workspace.py`](file:///d:/agency/src/infrastructure/coding/workspace.py) | **Implemented and verified** | Isolated git worktrees for concurrent developers, branch merge lock. |
| **Studio Task Execution** | [`src/application/studio_service.py`](file:///d:/agency/src/application/studio_service.py) | **Broken or inconsistent** | Runs via in-process `asyncio.create_task` in API process; dies on restart. |
| **Command Execution Sandbox** | [`src/infrastructure/coding/command_runner.py`](file:///d:/agency/src/infrastructure/coding/command_runner.py) | **Partially implemented** | Enforces command allowlists and path checks, but executes unconfined on host. |
| **Sandboxed Benchmark Runner** | [`src/infrastructure/coding/sandboxed_runner.py`](file:///d:/agency/src/infrastructure/coding/sandboxed_runner.py) | **Implemented and verified** | Ephemeral directory isolation and env scrubbing for benchmarks. |
| **Tenant Isolation Middleware** | [`src/api/middleware/tenant.py`](file:///d:/agency/src/api/middleware/tenant.py) | **Partially implemented** | Web requests carry tenant context; background/admin tasks can lose it. |
| **Tool Approval Engine** | [`src/application/tool_approval_service.py`](file:///d:/agency/src/application/tool_approval_service.py) | **Broken or inconsistent** | Approvals not bound to parameter hashes, workspaces, or single-use tokens. |
| **Disaster Recovery Engine** | [`src/application/disaster_recovery_engine.py`](file:///d:/agency/src/application/disaster_recovery_engine.py) | **Mocked or simulated** | Snapshots stored in RAM (`dict`); no physical database or S3 backup. |
| **Audit Hash-Chain V2** | [`src/application/audit_governance_v2.py`](file:///d:/agency/src/application/audit_governance_v2.py) | **Broken or inconsistent** | Non-atomic write operations; in-memory cache forks under concurrent writes. |
| **CEO Autonomous Planner** | [`src/application/company_operating_cycle_service.py`](file:///d:/agency/src/application/company_operating_cycle_service.py) | **Partially implemented** | 10-state operating cycle exists, but general-purpose outcome DAG intake is missing. |
| **Research & Innovation** | [`src/application/research_services.py`](file:///d:/agency/src/application/research_services.py) | **Implemented and verified** | Research questions, evidence collection, hypotheses, and report generation. |
| **Dynamic Swarms** | [`src/application/swarm_service.py`](file:///d:/agency/src/application/swarm_service.py) | **Implemented and verified** | Capability-based swarm clustering, coordination modes, and conflict resolver. |
| **Transactional Outbox Worker** | [`src/infrastructure/worker.py`](file:///d:/agency/src/infrastructure/worker.py) | **Partially implemented** | Relays outbox events to Redis/logs; does not execute background agent jobs. |
| **2D Isometric Pixel Office** | [`frontend/src/studio/office/scene.ts`](file:///d:/agency/frontend/src/studio/office/scene.ts) | **Implemented and verified** | Live WebSocket visualization of working, testing, meetings, leisure states. |
| **Mobile Mission Control** | — | **Missing** | Responsive layout exists, but no dedicated mobile app or mobile push/voice. |
| **Connected Local PC Agent** | — | **Missing** | Lightweight daemon for remote Windows/Linux access not yet built. |
| **Browser Execution Subsystem** | — | **Missing** | Full headless browser with DOM inspection, screenshots, takeover is missing. |
| **Multi-Tier Memory Architecture**| [`src/domain/memory.py`](file:///d:/agency/src/domain/memory.py), [`src/application/memory_service.py`](file:///d:/agency/src/application/memory_service.py) | **Partially implemented** | Basic memory items exist; scoped Org/Owner/Project/Employee memory missing. |

---

## 4. Deep-Dive Audit of the 8 Known Risk Areas

### Finding 1: In-Process Studio Execution & Lack of Durable Queue
* **File Path**: [`src/application/studio_service.py#L90-L93`](file:///d:/agency/src/application/studio_service.py#L90-L93), [`src/application/studio_service.py#L207-L211`](file:///d:/agency/src/application/studio_service.py#L207-L211)
* **Evidence**:
  ```python
  self._tasks: dict[str, asyncio.Task[DevProject]] = {}
  ...
  task = asyncio.create_task(
      orchestrator.run_project(project_id, should_cancel=lambda: project_id in self._cancelled),
      name=f"studio-{project_id}",
  )
  self._tasks[project_id] = task
  ```
* **Severity**: **CRITICAL**
* **Impact**: If the API server process restarts, crashes, or is redeployed in a container, all active developer and manager tasks are terminated immediately. Projects are left in `RUNNING` or `PLANNING` indefinitely with no worker leases or heartbeat recovery.
* **Proposed Correction**:
  1. Decouple project execution from the FastAPI web server.
  2. Implement a durable job queue with persistent execution records, worker leases, and heartbeats.
  3. Transform `src/infrastructure/worker.py` into a genuine agent worker daemon that claims jobs using atomic leases.
* **Acceptance Criteria**:
  * Killing the API process during an active project run does not abort the background worker.
  * When a worker process crashes, its expired lease is detected and reclaimed by another worker without duplicating external actions.

---

### Finding 2: Lack of OS-Level Containerization in CommandRunner
* **File Path**: [`src/infrastructure/coding/command_runner.py#L4-L8`](file:///d:/agency/src/infrastructure/coding/command_runner.py#L4-L8), [`#L130-L160`](file:///d:/agency/src/infrastructure/coding/command_runner.py#L130-L160)
* **Evidence**:
  ```python
  # "This is a policy boundary, not an OS sandbox: an allowed program can still reach the network and the rest of the filesystem. Run the API inside a container/VM for hard isolation."
  proc = await asyncio.create_subprocess_exec(
      argv[0], *argv[1:], cwd=str(cwd), env=env, stdout=..., stderr=...
  )
  ```
* **Severity**: **HIGH**
* **Impact**: Although dangerous binaries and shell operators are filtered, permitted programs (`python`, `node`, `npm`, `pytest`) run unconfined on the host operating system. A model could install a malicious npm dependency, inspect system environment files, or open unauthorized outbound network connections.
* **Proposed Correction**:
  1. Integrate Docker/container execution into the default runtime pipeline.
  2. For local non-containerized runs, enforce strict directory jails, read-only system binds, and network namespace restrictions where supported.
* **Acceptance Criteria**:
  * Code executed by a developer agent cannot read files outside the designated workspace root.
  * Host network access during testing can be disabled or restricted to configured proxies.

---

### Finding 3: Tenant Context Drift in Background and Administrative Paths
* **File Path**: [`src/api/middleware/tenant.py#L19-L26`](file:///d:/agency/src/api/middleware/tenant.py#L19-L26), [`src/application/studio_service.py#L99`](file:///d:/agency/src/application/studio_service.py#L99)
* **Evidence**:
  Tenant propagation relies on Python `contextvars` (`_current_tenant_id`). When tasks are spawned via `asyncio.create_task` or invoked from CLI scripts (`run_studio_project.py`), the context variable is `None`. If `create_project` is called without explicit `tenant_id`, it defaults to `None`, bypassing tenant scoping in repositories.
* **Severity**: **HIGH**
* **Impact**: Cross-tenant data leakage or orphan records that belong to no tenant and are visible to administrative queries.
* **Proposed Correction**:
  1. Make `tenant_id` a mandatory, non-nullable field on `DevProject`, `Task`, `Execution`, and all domain entities.
  2. Explicitly bind `tenant_id` into every worker execution context and background task runner.
* **Acceptance Criteria**:
  * All database operations fail if an active tenant context is not bound.
  * Cross-tenant read/write tests consistently raise `PermissionDenied`.

---

### Finding 4: Unbound Approval Grants Vulnerable to Reuse and Tampering
* **File Path**: [`src/domain/tool.py#L255-L265`](file:///d:/agency/src/domain/tool.py#L255-L265), [`src/application/tool_approval_service.py#L42-L49`](file:///d:/agency/src/application/tool_approval_service.py#L42-L49)
* **Evidence**:
  ```python
  approval = ToolApproval(
      id=approval_id,
      execution_id=execution.id,
      tool_id=execution.tool_id,
      capability=execution.capability,
      requester_employee_id=requester_employee_id,
      status=ApprovalStatus.PENDING,
  )
  ```
* **Severity**: **HIGH**
* **Impact**: The approval entity does not record:
  * A hash of the exact parameters being executed.
  * The specific workspace or repository target.
  * The tenant ID.
  * A single-use consumption flag or expiration time (TTL).
  An agent could request approval for `write_file(path='test.txt')`, receive approval, and then execute `write_file(path='/etc/hosts')` using the same `approval_id`.
* **Proposed Correction**:
  1. Add `parameter_hash`, `tenant_id`, `workspace_root`, `expires_at`, and `consumed_at` to `ToolApproval`.
  2. The tool pipeline must verify `sha256(canonical_json(parameters)) == approval.parameter_hash` and mark the approval consumed immediately.
* **Acceptance Criteria**:
  * Modifying any tool parameter after approval causes execution to be rejected.
  * An approval cannot be reused across executions or workspaces.

---

### Finding 5: In-Memory Disaster Recovery Snapshots
* **File Path**: [`src/application/disaster_recovery_engine.py#L34-L51`](file:///d:/agency/src/application/disaster_recovery_engine.py#L34-L51)
* **Evidence**:
  ```python
  self._snapshots: Dict[str, BackupSnapshot] = {}
  ...
  snapshot = BackupSnapshot(...)
  self._snapshots[snapshot_id] = snapshot
  ```
* **Severity**: **HIGH**
* **Impact**: All disaster recovery snapshot catalogs, backup manifests, and SLA tracking items are stored in a volatile in-memory dictionary. A crash wipes the recovery catalog. No physical database dump (`pg_dump` or SQLite vacuum) is executed or uploaded to MinIO/S3.
* **Proposed Correction**:
  1. Persist `BackupSnapshot` records to the database with a dedicated Alembic migration.
  2. Implement an actual backup pipeline that takes physical database dumps, signs them, and streams them to S3/MinIO.
  3. Implement an automated restoration drill script with checksum verification.
* **Acceptance Criteria**:
  * Restarting the server preserves all backup snapshot records.
  * A simulated database corruption can be restored from the latest snapshot and verified.

---

### Finding 6: Audit Hash-Chain Race Conditions and Cache Drift
* **File Path**: [`src/application/audit_governance_v2.py#L14-L37`](file:///d:/agency/src/application/audit_governance_v2.py#L14-L37)
* **Evidence**:
  ```python
  chain = self._chain(tenant_id)
  prev_hash = chain[-1].hash if chain else "GENESIS"
  record = AuditRecordV2(..., prev_hash=prev_hash)
  record.hash = record.compute_hash()
  chain.append(record)
  ```
* **Severity**: **HIGH**
* **Impact**:
  1. `record_action()` is synchronous and lacks database-level row locking (`SELECT FOR UPDATE`) or atomic sequence numbers.
  2. Two concurrent requests for the same tenant will read the identical `prev_hash`, fork the chain, and permanently corrupt `verify_audit_chain()`.
  3. `self._audit_chains` in-memory dictionary drifts across multi-process workers.
* **Proposed Correction**:
  1. Remove the in-memory cache `self._audit_chains`.
  2. Use a database transaction with a tenant-scoped sequence lock or atomic `INSERT INTO ... SELECT` to guarantee monotonic ordering.
  3. Support periodic checkpointing for fast verification.
* **Acceptance Criteria**:
  * Concurrency tests running 50 simultaneous audit writes across 4 processes maintain 100% hash-chain integrity with zero forks.

---

### Finding 7: Infrastructure Security & Exposed Ports
* **File Path**: [`docker-compose.yml#L12-L43`](file:///d:/agency/docker-compose.yml#L12-L43)
* **Evidence**:
  * PostgreSQL port `5432:5432`, Redis `6379:6379`, and MinIO `9000:9000`/`9001:9001` are bound to all interfaces (`0.0.0.0`).
  * Default development passwords (`postgrespassword`, `minioadminpassword`) are hardcoded in the compose file.
* **Severity**: **MEDIUM**
* **Impact**: If deployed on a host with a public IP without external firewalling, critical databases are exposed to internet scanners.
* **Proposed Correction**:
  1. Bind internal infrastructure ports to `127.0.0.1:5432`, etc., in development, or keep them within the internal Docker bridge network without host port publication.
  2. Enforce environment variable substitution (`${POSTGRES_PASSWORD:?err}`) and provide a production compose template.
* **Acceptance Criteria**:
  * Infrastructure ports are inaccessible from outside localhost.
  * Production containers fail to start if default credentials are used.

---

### Finding 8: Documentation Discrepancies
* **File Path**: [`progress.md`](file:///d:/agency/progress.md), [`README.md`](file:///d:/agency/README.md), [`docs/production.md`](file:///d:/agency/docs/production.md)
* **Evidence**:
  * `progress.md` cites **527 tests** and **20 migrations**.
  * Reality: **852 tests** collected in pytest and **40 migrations** (`001` through `040`).
* **Severity**: **LOW**
* **Proposed Correction**: Update all project documentation, status trackers, and readme badges to reflect the verified numbers.

---

## 5. Audit Conclusion

The Autonomous Agency codebase has strong core primitives: robust domain entities, comprehensive test suites (852 tests), a working Software Studio with Git worktree concurrency, and rich enterprise domain models.

However, it currently functions as a **desktop/API-coupled development tool** rather than a **durable, persistent AI operating system**. The immediate priority is not to write new end-user features, but to stabilize the foundation:
1. Move background execution to durable queues and worker processes.
2. Fix security boundaries (approval binding, audit concurrency, OS sandboxing).
3. Connect the CEO planning engine to true outcome-based DAG decomposition.

