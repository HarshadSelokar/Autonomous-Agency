# Autonomous AI Organization Platform — Phase 1 to Phase 14

This repository implements **Phases 1–14** of the Autonomous AI Organization Platform, including the Phase 14 Enterprise Department Expansion, Cross-Department Requests, Evidence-Verified Handoffs, and Multi-Department Collaboration Framework over the unified Company OS.

## Core Architectural Principle

$$\text{Company} \rightarrow \text{Departments} \rightarrow \text{Managers} \rightarrow \text{Employees} \rightarrow \text{Agents} \rightarrow \text{Tasks} \rightarrow \text{Tools} \rightarrow \text{Evidence} \rightarrow \text{Verification}$$

$$\text{DEPARTMENTS PROVIDE SPECIALIZATION. COMPANY OS PROVIDES COORDINATION.}$$

$$\text{EMPLOYEE} \neq \text{AGENT} \neq \text{LLM} \neq \text{DEPARTMENT} \neq \text{PIXEL OFFICE}$$

- **Employee**: Represents organizational identity, corporate title, department membership, skills, capabilities, responsibilities, manager delegation hierarchy, and lifecycle state (`INACTIVE`, `ACTIVE`, `ON_LEAVE`, `SUSPENDED`, `TERMINATED`).
- **Agent**: Represents execution capabilities, permission profile, model configuration, and state machine (`IDLE` → `READY` → `RUNNING`).
- **LLM**: Model provider capability (e.g. Groq `llama-3.3-70b-versatile`) invoked by the Agent Runtime engine.

---

## Organizational Chain of Command

$$\text{Objective} \rightarrow \text{Plan} \rightarrow \text{WorkItem} \rightarrow \text{Assignment} \rightarrow \text{Employee} \rightarrow \text{AgentRun}$$

1. **Objective**: High-level corporate objective received from stakeholders.
2. **Plan**: Strategic decomposition proposed by a Manager employee.
3. **WorkItem**: Atomically scoped task unit requiring specific capabilities.
4. **Assignment**: Match allocation connecting WorkItem to an active Employee.
5. **Employee Execution**: Work delegated to the Employee's underlying Agent via Phase 1 `AgentExecutionEngine`.

---

## Quick Start & Running Demonstrations

### 1. Run Full Test Suite (141 Unit, Integration & Failure-Injection Tests)
```bash
pytest
```

### 2. Run Phase 3 Demonstration Scripts
```bash
# Phase 3: Manager goal decomposition, capability allocation & blocker resolution demo
python scripts/demo_manager_orchestration.py

# Phase 3: Hierarchy cycle detection, plan validation & guardrails resilience demo
python scripts/demo_manager_resilience.py
```

### 3. Run Phase 1 & Phase 2 Demonstration Scripts
```bash
python scripts/demo_employee_execution.py
python scripts/demo_employee_resilience.py
python scripts/demo_research_agent.py
python scripts/demo_failure_recovery.py
```

### 4. Run FastAPI REST API Server
```bash
uvicorn src.api.main:app --reload --port 8000
```

---

## Key API Endpoints

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Objectives** | `/objectives` | `POST` | Create new organizational objective |
| **Objectives** | `/objectives/{id}` | `GET` | Retrieve objective status and associated plan |
| **Clarification** | `/objectives/{id}/clarification/request` | `POST` | Request ambiguity clarification questions |
| **Clarification** | `/objectives/{id}/clarification/provide` | `POST` | Provide clarification answers |
| **Planning** | `/objectives/{id}/plans` | `POST` | Manager submits proposed decomposition plan |
| **Planning** | `/objectives/plans/{plan_id}/approve` | `POST` | Manager approves proposed plan |
| **Work Items** | `/objectives/work-items/{id}/assign` | `POST` | Allocate work item to eligible employee |
| **Work Items** | `/objectives/work-items/{id}/blocker` | `POST` | Log work item blocker escalation |
| **Work Items** | `/objectives/work-items/{id}/reassign` | `POST` | Manager reassigns blocked work item |
| **Employees** | `/employees` | `POST` | Onboard new corporate employee |
| **Employees** | `/employees/{id}/status` | `POST` | Transition employee lifecycle state |
| **Employees** | `/employees/{id}/runs` | `POST` | Execute organizational work via Agent Runtime |

---

## Project Structure

- `src/domain/`: Pure domain entities (`Objective`, `Plan`, `WorkItem`, `Assignment`, `ManagerDecision`, `Employee`, `Department`, `Agent`), lifecycle state machines, domain events, exceptions, interfaces.
- `src/application/`: `ManagerOrchestrationService`, `PlanValidator`, `EmployeeSelector`, `EmployeeService`, `AgentExecutionEngine`, `EventDispatcher`.
- `src/infrastructure/`: Groq SDK provider (`GroqModelProvider`), Fake provider, PostgreSQL/SQLite ORM models and repositories (`SQLAlchemyObjectiveRepository`, `SQLAlchemyPlanRepository`, `SQLAlchemyWorkItemRepository`, `SQLAlchemyAssignmentRepository`, `SQLAlchemyDecisionRepository`, `SQLAlchemyEmployeeRepository`, `SQLAlchemyAgentRepository`), Alembic migrations (`006_create_phase3_tables.py`).
- `src/api/`: FastAPI REST endpoints (`/objectives`, `/employees`, `/agents`, `/runs`), Pydantic DTO schemas.
- `tests/`: Unit, integration, and failure injection test suites (`test_manager_failure_injection.py`).
- `scripts/`: End-to-end demonstration scripts for Phase 1, Phase 2, and Phase 3.
- `docs/`: Architecture specifications and Mermaid sequence diagrams (`docs/architecture.md`).
