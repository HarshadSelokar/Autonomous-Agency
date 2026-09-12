# Autonomous AI Organization Platform — Phase 1 & Phase 2

This repository implements the **Agent Runtime Foundation (Phase 1)** and **Employee Framework (Phase 2)** for the Autonomous AI Organization Platform.

## Core Architectural Principle

$$\text{EMPLOYEE} \neq \text{AGENT} \neq \text{LLM}$$

- **Employee**: Represents organizational identity, title, department membership, skills, capabilities, responsibilities, manager delegation hierarchy, and lifecycle state (`INACTIVE`, `ACTIVE`, `ON_LEAVE`, `SUSPENDED`, `TERMINATED`).
- **Agent**: Represents execution capabilities, permission profile, model configuration, and state machine (`IDLE` → `READY` → `RUNNING`).
- **LLM**: Model provider capability (e.g. Groq `llama-3.3-70b-versatile`) invoked by the Agent Runtime engine.

---

## Architectural Boundary

```
Company OS  →  Employee Framework  →  Agent Runtime  →  Model Provider Interface  →  GroqModelProvider
```

- **The LLM is NOT the Agent**: An LLM is only a provider used by the runtime.
- **Authoritative State**: Owned by the Agent Runtime & Company OS, never directly by the LLM.
- **Provider Independence**: Pure domain & application layers decoupled from Groq or any specific LLM provider.

---

## Quick Start & Running Demonstrations

### 1. Run All Tests (90 Unit, Integration & Failure-Injection Tests)
```bash
pytest
```

### 2. Run Phase 2 Demonstration Scripts
```bash
# Employee Framework execution & organizational context delegation
python scripts/demo_employee_execution.py

# Employee governance, state machine & guardrails resilience demo
python scripts/demo_employee_resilience.py
```

### 3. Run FastAPI REST API Server
```bash
uvicorn src.api.main:app --reload --port 8000
```

---

## Directory Structure

- `src/domain/`: Pure domain entities (`Employee`, `Department`, `Agent`, `AgentRun`, `ExecutionStep`), lifecycle state machines, domain events, exceptions, interfaces.
- `src/application/`: `EmployeeService`, `AgentExecutionEngine`, `EmployeeLoader`, `AgentLoader`, `EventDispatcher`, context builder, retry logic, structured output validator.
- `src/infrastructure/`: Groq SDK integration (`GroqModelProvider`), Fake provider, PostgreSQL/SQLite ORM repositories (`SQLAlchemyEmployeeRepository`, `SQLAlchemyDepartmentRepository`, `SQLAlchemyAgentRepository`), Alembic migrations.
- `src/api/`: FastAPI REST endpoints (`/employees`, `/agents`, `/runs`), Pydantic request/response DTO schemas.
- `config/`: Configuration-driven YAML definitions for Agents (`config/agents/`) and Employees (`config/employees/`).
- `tests/`: Unit, integration, and failure injection test suites.
- `scripts/`: Phase 1 and Phase 2 demonstration scripts.
- `docs/`: System architecture specification and Mermaid sequence diagrams.
