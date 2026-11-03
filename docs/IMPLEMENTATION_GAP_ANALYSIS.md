# Autonomous Agency — Implementation Gap Analysis
**Date:** November 2026  
**Document Version:** 1.0  
**Baseline:** Current Codebase vs. Target Master Project Directive  

---

## 1. Executive Summary

This gap analysis compares the existing **Autonomous Agency** codebase against the **Master Project Directive**. 

While the repository has rich domain entities (departments, employees, swarms, financial governance) and a functional Software Studio with Git worktree isolation, it currently functions as a **single-node, API-coupled application**. Significant architectural evolution is required to elevate it into a **persistent, distributed AI operating system** that can be operated from a mobile phone and executed across a hybrid fabric of cloud servers, local PCs, and isolated containers.

---

## 2. Subsystem-by-Subsystem Gap Matrix

| Target Subsystem | Master Directive Target | Current Implementation | Gap Severity | Primary Deficiencies |
| :--- | :--- | :--- | :--- | :--- |
| **1. Control / Execution Separation** | Standalone worker daemons; durable job queue; worker leases; API restarts do not interrupt work. | All executions run as in-process `asyncio.create_task` inside FastAPI (`StudioService`). `worker.py` only processes outbox events. | **CRITICAL** | Zero durability across process restarts; no worker heartbeats, leases, or distributed task queues. |
| **2. CEO Planning Engine** | Outcome-driven intake ("Investigate X, build Y, test Z"); multi-department DAG; dynamic replanning on blockers. | `MANAGER_PROMPT` in `dev_team_service.py` creates a flat list of coding tickets for 1 team. Operating cycle in domain is separate. | **HIGH** | Cannot ingest multi-domain organizational goals; cannot delegate across departments or synthesize cross-functional workflows. |
| **3. Persistent Agent Runtime** | Standardized runtime contract (`execute`, `cancel`, `get_status`, `recover`); worker leases; idempotency keys. | `LoopEngine` and `AgyEngine` with basic ReAct loop; in-memory task tracking. | **HIGH** | No unified runtime protocol; no checkpoint restoration or worker crash recovery. |
| **4. Hybrid Execution Fabric** | 3 environments: Agency Cloud Linux, Connected Local PC Agent (Windows/Linux outbound TLS), Isolated Container Workers. | Single host environment (wherever the API is running). | **HIGH** | Cannot connect to owner's local PC; cannot route tasks based on hardware, local repos, or cloud resources. |
| **5. Universal Tool Ecosystem** | Unified registry across 7 categories; input/output schemas; parameter-bound approvals; versioned contracts. | Hardcoded `CodingToolbox` (7 coding tools); legacy `tool_registry.py` disconnected from studio. | **HIGH** | No browser, data analysis, document generation, or business ops tools in the unified runtime. |
| **6. Browser Automation Subsystem** | Isolated sessions, DOM/accessibility trees, screenshots, file upload/download, remote owner takeover. | Only basic HTTP tool and mock search; no actual browser automation engine. | **HIGH** | No real browser agent; no visual takeover or session persistence. |
| **7. Multi-Tier Persistent Memory** | Scoped memory (Owner, Org, Project, Employee, Execution); semantic + keyword retrieval; privacy boundaries. | Flat `MemoryItem` table in database; basic retrieval without scoped isolation. | **MEDIUM** | No hierarchical memory scoping; no cross-project knowledge synthesis or retention rules. |
| **8. Proactive Responsibility Engine** | Ongoing responsibilities (CI monitoring, dependency updates, security alerts) running on triggers/schedules. | Strictly reactive; tasks only start when an explicit API call is received. | **MEDIUM** | No background opportunity discovery, continuous maintainers, or scheduled proactive tasks. |
| **9. Mobile Mission Control** | First-class mobile command center; voice intake; push notifications; remote pause/resume/takeover; offline resilience. | Responsive web UI (`Root.tsx` / `StudioApp.tsx`); no push notifications, voice processing, or takeover. | **MEDIUM** | No dedicated mobile view; no offline synchronization or remote device approval interface. |
| **10. Independent Proof-of-Work** | Formal verification engine producing cryptographically signed deliverables, test evidence, citations, and audits. | Deterministic QA test commands for code; LLM diff review. Enterprise verifier exists in domain. | **MEDIUM** | Lacks formal artifact proof bundles, signed evidence chains, and non-software verification. |
| **11. Security Sandboxing** | OS-level container isolation (Docker/gVisor), network egress policies, resource quotas, secure approval tokens. | Software allowlist in `CommandRunner`; unconfined host OS execution; unbounded approval tokens. | **CRITICAL** | Host filesystem and network accessible to child processes; approval grants vulnerable to parameter substitution. |

---

## 3. Detailed Gap Descriptions & Remediation Path

### Gap 1: Execution Durability & Worker Separation
* **Current State**:
  * In [`src/application/studio_service.py`](file:///d:/agency/src/application/studio_service.py), project runs are tracked via `self._tasks: dict[str, asyncio.Task]`.
  * If the API server is restarted (e.g. during a deployment or error), all in-flight coroutines die instantly.
  * The project status remains locked in `RUNNING` or `PLANNING`.
* **Required Transformation**:
  1. Introduce a persistent `JobQueue` / `TaskExecutionRecord` in PostgreSQL with row-level leasing (`status = 'CLAIMED', worker_id = '...', lease_expires_at = '...'`).
  2. Implement worker heartbeats updating `lease_expires_at` every 15 seconds.
  3. Transform [`src/infrastructure/worker.py`](file:///d:/agency/src/infrastructure/worker.py) into a real agent execution daemon that polls and claims jobs.
  4. Build a dead-letter detector that transitions expired leases to `FAILED` or re-assigns them to healthy workers.

---

### Gap 2: From Linear Ticket Manager to CEO Outcome DAG Planner
* **Current State**:
  * [`src/application/dev_team_service.py`](file:///d:/agency/src/application/dev_team_service.py) uses `MANAGER_PROMPT` to break a goal into 1-12 tickets for a single engineering team.
  * The 22-phase Enterprise OS (`src/domain/software_company.py`, `department.py`, `swarm.py`) exists as an isolated simulation.
* **Required Transformation**:
  1. Create an executive **CEO Agent** capable of receiving broad outcomes (e.g., "Research competing frameworks, build a benchmark prototype, run tests, and publish results").
  2. Decompose outcomes into a cross-department Directed Acyclic Graph (DAG) involving Research, Engineering, QA, and Documentation.
  3. Dynamic employee assignment: map subtasks to specialized employees based on capability profiles rather than hardcoded roles.
  4. Dynamic replanning: if a dependency fails or a tool encounters a blocker, the CEO re-routes or re-evaluates the DAG.

---

### Gap 3: Execution Sandboxing & Hybrid Fabric
* **Current State**:
  * [`CommandRunner`](file:///d:/agency/src/infrastructure/coding/command_runner.py) executes commands directly on the host using `asyncio.create_subprocess_exec`.
  * The server has no mechanism to interact with the owner's laptop or separate cloud workers.
* **Required Transformation**:
  1. **Containerized Worker Sandbox**: Replace host execution with ephemeral Docker containers or gVisor sandboxes with restricted network egress, resource limits (CPU/RAM), and workspace-only volume mounts.
  2. **Connected Local Agent**: Build a lightweight Python/Go daemon (`agency-agent`) that the user runs on Windows/Linux. It establishes a secure outbound WebSocket/mTLS connection to the Agency Control Plane, registers local capabilities (e.g., local VS Code workspaces, GPUs, private repositories), and executes only explicitly authorized commands.
  3. **Environment Router**: Routes tasks to Cloud Workers, Local PC, or Container Sandboxes based on required tools, hardware, and data location.

---

### Gap 4: Universal Tool Ecosystem & Secure Approval Binding
* **Current State**:
  * Coding tools are implemented directly in [`src/infrastructure/coding/toolbox.py`](file:///d:/agency/src/infrastructure/coding/toolbox.py).
  * `ToolApproval` in [`src/domain/tool.py`](file:///d:/agency/src/domain/tool.py) records `tool_id` and `execution_id`, but does not bind parameters or workspace paths.
* **Required Transformation**:
  1. Build a unified `ToolRegistry` with standardized schemas for:
     * Development (Terminal, Git, Build, Test).
     * Browser (Playwright-based navigation, clicking, screenshots, form filling).
     * Research (Web search, page extraction, PDF parsing).
     * Data (Python dataframes, SQL queries, visualizations).
     * Productivity & Business (PDF, DOCX, email, tickets).
  2. Cryptographically bind approvals:
     ```python
     expected_hash = hashlib.sha256(canonical_json(parameters)).hexdigest()
     assert approval.parameter_hash == expected_hash
     assert approval.workspace_root == current_workspace
     assert not approval.is_consumed
     approval.consume()
     ```

---

### Gap 5: Mobile Mission Control & Interactive Takeover
* **Current State**:
  * The frontend is accessible via web browsers, but has no mobile-optimized controls, push notification channels, or remote execution controls.
* **Required Transformation**:
  1. Build mobile-first endpoints and UI components:
     * Mission Control overview (active tasks, budget, pending approvals).
     * Mobile Approval Inbox with one-tap approve/reject and exact diff/parameter views.
     * Remote execution pause, redirection, and emergency stop kill switch.
     * Webhook/Push notification integration (Web Push / Expo) for critical events and approval requests.
  2. Live Browser / Workspace Takeover: Allow the user to pause an agent, view the workspace/browser state, make adjustments, and return control seamlessly.

