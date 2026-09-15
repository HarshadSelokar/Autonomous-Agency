# Phase 15 — Dynamic Workforce, Capability-Based Staffing & Autonomous Team Formation

## 1. Executive Summary

Phase 15 introduces the **Dynamic Workforce Engine** to the Autonomous AI Organization Platform. It transforms static workforce assumptions into a dynamic, capability-based staffing and team-formation architecture.

The Company OS understands:
- **Work Demand**: Derived from Company/Department Objectives, Projects, and Task Graphs.
- **Capability Requirements**: Structured capability, proficiency, duration, and priority specifications.
- **Employee Capacity**: Measurable capacity snapshots (`1.0 - allocated_capacity`).
- **Capability Gaps**: Deterministic gap calculation (`Demand - Available Capacity = Capability Gap`).
- **Staffing Recommendations**: Multi-factor explainable scoring (`Capability Fit + Availability + Workload Fit + Reliability - Penalties`).
- **Governed Teams**: Creation, activation, allocation, and dissolution of temporary and cross-department project teams.
- **Controlled Provisioning**: Consequential workforce changes (new employee provisioning, privilege changes, employee termination) MUST pass Phase 11 Human Governance approval.

---

## 2. Core Architectural Principles & Invariants

### 2.1 Governance & Autonomy Invariants
- **EMPLOYEE != AGENT != LLM != TEAM != DEPARTMENT != MODEL**
- **WORKFORCE ENGINE != GOVERNANCE != TASK ENGINE != AGENT RUNTIME**
- The Workforce Engine **MUST NOT** become an uncontrolled autonomous hiring/firing system.
- Autonomous self-approval or self-expanding hiring without governance is strictly prohibited.
- **No Automatic Termination**: Employee lifecycle remains governed. Reliability or low workload metrics never trigger automated termination.

---

## 3. Workflow Lifecycle

```
                 COMPANY OBJECTIVES / PROJECTS / TASK GRAPH
                                     │
                                     ▼
                            WORKFORCE DEMAND
                                     │
                                     ▼
                            CAPABILITY ANALYSIS
                                     │
                                     ▼
                            CAPACITY SNAPSHOTS
                                     │
                                     ▼
                         CAPABILITY GAP DETECTION
                                     │
                                     ▼
                      STAFFING RECOMMENDATIONS (EXPLAINABLE)
                                     │
                                     ▼
                             HUMAN GOVERNANCE
                                     │
                                     ▼
                             MANAGER DECISION
                                     │
                                     ▼
                      DYNAMIC TEAM FORMATION & ALLOCATION
                                     │
                                     ▼
                           EXISTING TASK ENGINE
                                     │
                                     ▼
                       VERIFICATION & COMPLETION
                                     │
                                     ▼
                            TEAM DISSOLUTION
```

---

## 4. Key Entities & Services

### 4.1 Domain Entities (`src/domain/workforce.py`, `src/domain/team.py`)
- `WorkforceDemand`: ID, source_type, source_id, department_id, capability, required_count, priority, duration_days, deadline, risk_level, governance_required.
- `CapacitySnapshot`: ID, employee_id, capability, max_capacity, allocated_capacity, available_capacity, active_assignments_count.
- `CapabilityGap`: ID, capability, required_count, available_count, gap_count, severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), affected_project_ids.
- `StaffingRecommendation`: ID, demand_id, candidate_employee_ids, capability_fit_score, availability_score, workload_score, reliability_score, final_score, reasoning.
- `Team`: ID, name, code, purpose, team_type (`PROJECT`, `DEPARTMENTAL`, `CROSS_DEPARTMENT`, `TEMPORARY`), status (`PROPOSED`, `FORMING`, `ACTIVE`, `PAUSED`, `DISSOLVING`, `DISSOLVED`), capabilities (derived).
- `TeamMember`: ID, team_id, employee_id, role_in_team, allocation_percentage, assigned_at, removed_at.

### 4.2 Application Services (`src/application/`)
- `WorkforcePlanningService`: Manages demand creation, capacity calculation, gap detection, explainable recommendation generation, and workforce plan creation.
- `TeamFormationService`: Manages governed team creation, member allocations, change requests, governance checks, team activation, team dissolution, and controlled employee provisioning.

---

## 5. REST API Surface (`src/api/routes/`)

- `POST /workforce/demands` — Create workforce demand
- `GET /workforce/demands` — List demands
- `GET /workforce/gaps` — Detect & list capability gaps
- `POST /workforce/recommendations` — Generate staffing recommendations
- `POST /workforce/requests` — Submit governed workforce change requests
- `POST /workforce/requests/{id}/approve` — Approve workforce change request
- `GET /workforce/health` — Retrieve workforce health status
- `POST /teams` — Propose team
- `GET /teams` — List teams
- `GET /teams/{id}` — Get team details & members
- `POST /teams/{id}/members` — Add member & allocate to team
- `POST /teams/{id}/dissolve` — Dissolve team and release temporary allocations
