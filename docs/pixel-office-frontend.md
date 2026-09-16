# Phase 21 — Pixel Office Frontend & Real-Time Control Center Specification

This document details the architecture, design system, component hierarchy, state management, and real-time WebSocket protocol for the **Pixel Office Frontend** (Phase 21).

---

## 1. Architectural Philosophy

```
                    BACKEND COMPANY OS (Authoritative State)
                                     │
                                     ▼
                      REST APIS & WEBSOCKET EVENT STREAM
                                     │
                                     ▼
                    PIXEL OFFICE FRONTEND STATE LAYER
                                     │
                                     ▼
                      VISUAL 2D PROJECTION & CANVAS
```

### Core Invariants Enforced

* `PIXEL OFFICE != COMPANY OS` — The Pixel Office frontend is strictly a visual control center, observability dashboard, and governance projection layer.
* `PIXEL OFFICE != SOURCE OF TRUTH` — All organizational state, task statuses, employee allocations, governance approvals, and emergency stop statuses remain strictly authoritative on the backend.
* `NO INVENTED STATE` — The frontend visual representation strictly projects backend state events. Animations (working, thinking, recovering) represent actual backend events and never fabricate organizational activity.

---

## 2. Component Hierarchy & Navigation

```
                       AppShell
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
      Sidebar                           View Router
 (13 Nav Sections)                         │
                               ┌───────────┼───────────┐
                               ▼           ▼           ▼
                            Overview    Office      Dashboards
                           Dashboard    Canvas     (Governance,
                               │           │       Verification,
                               │           │        Recovery,
                               │           │       Infrastructure)
                               ▼           ▼           │
                               └───────> Drawers <─────┘
                                  (Employee, Task,
                                   Project, Meeting,
                                   Global Search)
```

### Navigational Views

1. **Company Overview**: High-level corporate health, active initiative counts, attention queue, recent activity log stream.
2. **Pixel Office Canvas**: Visual 2D interactive canvas rendering all 13 enterprise departments (Executive, Product, Engineering, QA, DevOps, Marketing, Sales, Customer Success, Finance, Legal, HR, Research, Operations), workstations, and active meeting rooms.
3. **Departments**: Department capacity, workload, manager, and team breakdowns.
4. **Dynamic Teams**: Dynamic workforce teams (`PROPOSED`, `FORMING`, `ACTIVE`, `PAUSED`, `DISSOLVING`, `DISSOLVED`).
5. **Software Projects**: AI Software Company delivery progress, task counts, blocked tasks.
6. **Tasks & DAG**: Work item state tracking (`CREATED` $\rightarrow$ `COMPLETED`), priorities, dependencies.
7. **Active Meetings**: Real-time meeting room participants, purpose, status, agenda.
8. **Governance Control**: Pending human approval actions, risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), autonomy levels, approval/rejection controls.
9. **Verification Engine**: Evidence verification status, rules, checks, and failed verification alerts.
10. **Failure Recovery**: Autonomous incident escalation, retries, and task rework status.
11. **Workforce Allocation**: Capability matching, workload distribution, and staffing capacity.
12. **Research & Innovation**: Phase 19 research programs, evidence integrity, hypotheses, and innovation proposals.
13. **Infrastructure Health**: Phase 20 operational monitoring (API, PostgreSQL pool, Redis, MinIO/S3, Outbox depth, Workers).

---

## 3. Real-time WebSocket Protocol & State Reconciliation

### Connection Lifecycle States

* **`CONNECTED`**: Active WebSocket stream connected to `/ws/office` (or `/office/ws`).
* **`DISCONNECTED`**: WebSocket connection lost; automatic reconnect timer active with exponential backoff.
* **`RECONNECTING`**: In-flight reconnection attempt.
* **`STALE`**: Reconnection limits exceeded or network unavailable. Frontend displays stale data banner.

### Snapshot Reconciliation Protocol

1. Client opens application and loads initial REST snapshot (`GET /office/overview`, `GET /office/employees`).
2. Client connects to WebSocket `/office/ws`.
3. Incoming events (`employee.updated`, `task.state_changed`, `governance.intervention`) mutate local state.
4. On reconnection, client invokes `GET /office/reconcile` and re-fetches authoritative REST snapshot to guarantee synchronization.

---

## 4. Human Governance & Emergency Stop

### Governance Actions
Consequential actions (approving or rejecting high-risk agent operations) call backend API endpoints (`POST /governance/approvals/{id}/approve` and `POST /governance/approvals/{id}/reject`).

### Global Emergency Stop
Human operators can click **EMERGENCY STOP** in the application shell. A high-risk modal requires text confirmation (`CONFIRM`) and a reason before issuing `POST /governance/emergency-stop`, which halts agent execution globally across the Company OS.
