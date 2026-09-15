# Phase 11 — Human Governance Architecture

## Overview

Human Governance in the Autonomous AI Organization Platform establishes an enterprise-grade policy, risk, authority, and approval engine. It enforces the foundational architectural rule:

> **Autonomy must be governed.**
> LLMs, Model Routers, and Agents MUST NEVER self-approve governed actions or bypass human policies.

```
HUMAN GOVERNANCE
        ↓
POLICY / RISK / AUTHORITY
        ↓
MODEL ROUTING
        ↓
AGENT EXECUTION
        ↓
TOOLS / VERIFICATION / RECOVERY
```

---

## Domain Concepts

### 1. Risk Hierarchy & Autonomy Levels (`src/domain/governance.py`)
- **Risk Levels**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **Autonomy Levels**:
  - `FULLY_AUTONOMOUS`: Executed without intervention.
  - `SUPERVISED`: Executed with automated logging and post-action audit.
  - `APPROVAL_REQUIRED`: Paused until human manager/admin approval is granted.
  - `HUMAN_ONLY`: Agent cannot execute; must be performed directly by a human.
  - `BLOCKED`: Forbidden action; blocked across scope.

### 2. Precedence Hierarchy
Governance policies are evaluated according to strict hierarchical precedence:
1. `SYSTEM` (Level 5) - Platform-wide security policies.
2. `COMPANY` (Level 4) - Enterprise policies.
3. `DEPARTMENT` (Level 3) - Departmental boundaries.
4. `PROJECT` (Level 2) - Project-specific controls.
5. `TASK` (Level 1) - Granular task constraints.

Higher precedence levels override lower levels.

### 3. Separation of Duties (Self-Approval Guard)
Any approval request explicitly enforces `prohibit_self_approval=True`. If the requesting actor attempts to approve their own request, `GovernanceService` blocks the action with HTTP 400 / `ValueError` and logs a `SEPARATION_OF_DUTIES_VIOLATION`.

### 4. Emergency Stop (Kill Switch)
Emergency stop state can be activated at `GLOBAL`, `COMPANY`, `DEPARTMENT`, `PROJECT`, `EMPLOYEE`, `AGENT`, `TASK`, or `TOOL` scope. When active, all governed executions within that scope are immediately blocked with `AutonomyLevel.BLOCKED`.

---

## Technical Components

- **Domain Model**: [`src/domain/governance.py`](file:///d:/agency/src/domain/governance.py)
- **Application Service**: [`src/application/governance_service.py`](file:///d:/agency/src/application/governance_service.py)
- **Persistence Layer**: [`src/infrastructure/models/governance_model.py`](file:///d:/agency/src/infrastructure/models/governance_model.py) & [`src/infrastructure/repositories/governance_repository.py`](file:///d:/agency/src/infrastructure/repositories/governance_repository.py)
- **REST API**: [`src/api/routes/governance.py`](file:///d:/agency/src/api/routes/governance.py)
