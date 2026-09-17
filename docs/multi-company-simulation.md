# Phase 25 — Multi-Company, Multi-Tenant Organization & Company Simulation Architecture

## 1. Executive Overview

Phase 25 transforms the Autonomous AI Organization Platform into a multi-company, multi-tenant enterprise framework capable of hosting and operating multiple isolated autonomous AI companies on shared production infrastructure. In addition to multi-tenant isolation, Phase 25 introduces a **What-If Company Simulation Engine** allowing executives, founders, and AI managers to simulate structural company changes, headcount growth, pricing adjustments, and market shocks in a sandbox environment with absolute isolation from production state.

### Key Architectural Invariants
```
TENANT != USER
COMPANY != EMPLOYEE
COMPANY != AGENT
REALITY != SIMULATION
SIMULATION != AUTHORITATIVE COMPANY STATE
COMPANY A != COMPANY B
```

1. **Strict Data & Resource Isolation**: Cross-company access is denied by default. Data access between distinct companies requires explicit relationship definition, data share requests, and human governance approval.
2. **Deterministic Safety Isolation**: Simulation execution strictly blocks real payment gateway calls, external email delivery, production database mutation, or contract signing.
3. **Resource Quotas & Capacity Control**: Each company is constrained by configurable resource quotas (Agents, Employees, Monthly Budget, Storage, API limits).

---

## 2. Multi-Tenant Architecture & Boundary Middleware

Every incoming request passes through the `CompanyContextMiddleware`, which resolves tenant context (`X-Company-ID`, `X-User-ID`, `X-Environment-ID`, `X-Simulation-ID`) and injects a `CompanyContext` into the request state.

```mermaid
graph TD
    Client[HTTP Client / Pixel Office UI] -->|X-Company-ID Header| Middleware[CompanyContextMiddleware]
    Middleware -->|Validate Tenant Context| Context[CompanyContext Object]
    Context --> Router[REST API Router]
    Router --> Service[Application Services]
    Service -->|Filter by company_id| Repo[SQLAlchemy Repository]
    Repo -->|Tenant Isolated SQL| DB[(PostgreSQL Database)]
```

---

## 3. Database Schema & ERD

Phase 25 adds 10 dedicated multi-tenant and simulation tables to PostgreSQL via Alembic Migration `024_create_phase25_multi_company_tables.py`.

```mermaid
erDiagram
    AUTONOMOUS_COMPANIES ||--o{ COMPANY_PROFILES : has
    AUTONOMOUS_COMPANIES ||--o{ COMPANY_MEMBERSHIPS : has
    AUTONOMOUS_COMPANIES ||--o{ COMPANY_RESOURCE_QUOTAS : constrained_by
    AUTONOMOUS_COMPANIES ||--o{ COMPANY_RESOURCE_USAGES : tracks
    AUTONOMOUS_COMPANIES ||--o{ COMPANY_RELATIONSHIPS : initiates
    AUTONOMOUS_COMPANIES ||--o{ COMPANY_DATA_SHARE_REQUESTS : requests
    AUTONOMOUS_COMPANIES ||--o{ COMPANY_SIMULATIONS : executes
    COMPANY_SIMULATIONS ||--o{ SIMULATION_SNAPSHOTS : references
    COMPANY_SIMULATIONS ||--o{ SIMULATION_SCENARIOS : applies
    COMPANY_SIMULATIONS ||--o{ SIMULATION_RESULTS : produces
    COMPANY_SIMULATIONS ||--o{ SIMULATION_FINANCIAL_RECORDS : generates
```

---

## 4. Company Lifecycle State Machine

Autonomous companies transition through strict lifecycle states enforced by `Company.transition_lifecycle()`.

```mermaid
stateDiagram-v2
    [*] --> PROPOSED
    PROPOSED --> INITIALIZING : Provision Resources
    PROPOSED --> ARCHIVED : Cancel
    INITIALIZING --> ACTIVE : Bootstrap Complete
    INITIALIZING --> ARCHIVED : Failed Setup
    ACTIVE --> PAUSED : Maintenance
    ACTIVE --> SUSPENDED : Quota / Compliance Breach
    ACTIVE --> ARCHIVED : Liquidation
    PAUSED --> ACTIVE : Resume Operations
    PAUSED --> SUSPENDED : Escalation
    PAUSED --> ARCHIVED : Terminate
    SUSPENDED --> ACTIVE : Remedy Compliance
    SUSPENDED --> ARCHIVED : Liquidation
    ARCHIVED --> [*]
```

---

## 5. What-If Simulation Sandbox Engine & Safety Boundaries

The Scenario Engine computes deterministic outcome projections based on baseline snapshots and scenario variables.

```mermaid
flowchart LR
    subgraph Production Environment
        ProdCompany[Company State]
        ProdDB[(Production DB)]
        Stripe[Stripe Gateway]
        SendGrid[SendGrid Email]
    end

    subgraph Simulation Sandbox Context
        Snapshot[Baseline Snapshot]
        Scenario[Scenario Variables]
        Engine[Scenario Calculation Engine]
        SimResult[Simulated Metrics Result]
        SimDB[(Simulated Financial Records)]
    end

    ProdCompany -->|Read-Only Point-In-Time Snapshot| Snapshot
    Snapshot --> Engine
    Scenario --> Engine
    Engine --> SimResult
    Engine --> SimDB

    Engine --x|BLOCKED| Stripe
    Engine --x|BLOCKED| SendGrid
    Engine --x|BLOCKED| ProdDB
```

---

## 6. Governed Cross-Company Data Sharing

Cross-company communication and data sharing require explicit relationship establishment, data share request submission, and human governance approval.

```mermaid
sequenceDiagram
    autonumber
    participant CompA as Company A (Source)
    participant Kernel as Multi-Tenant Kernel
    participant Gov as Human Governance Gateway
    participant CompB as Company B (Target)

    CompA->>Kernel: Create Relationship (PARTNER)
    Kernel-->>CompA: Relationship ACTIVE
    CompA->>Kernel: Request Data Share (READ_ONLY, Purpose)
    Kernel-->>Gov: Submit DataShareRequest (REQUESTED)
    Gov->>Kernel: Approve Request (governance_approval_id)
    Kernel-->>CompA: DataShareRequest APPROVED
    CompA->>Kernel: Access Shared Resource
    Kernel->>CompB: Read Filtered Resource Data
    Kernel-->>CompA: Return Shared Payload
```

---

## 7. Quota Enforcement Flowchart

```mermaid
flowchart TD
    Req[Action Request: Add Agent / Execute Task] --> FetchQuota[Fetch CompanyResourceQuota]
    FetchQuota --> CheckLimit{Current Usage + Requested <= Max Limit?}
    CheckLimit -- Yes --> Allow[Increment Resource Usage & Proceed]
    CheckLimit -- No --> Deny[Raise CompanyQuotaExceededError]
```

---

## 8. Simulation Engine Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Executive / Founder
    participant API as Simulation REST API
    participant Service as CompanySimulationService
    participant Engine as SimulationScenarioEngine
    participant Repo as MultiCompanyRepository

    User->>API: POST /api/v1/simulations/snapshots (Baseline Metrics)
    API->>Service: create_snapshot()
    Service->>Repo: save_simulation_snapshot()
    User->>API: POST /api/v1/simulations/scenarios (Variables)
    API->>Service: create_scenario()
    Service->>Repo: save_simulation_scenario()
    User->>API: POST /api/v1/simulations (Run Instance)
    API->>Service: create_simulation()
    Service->>Repo: save_simulation()
    User->>API: POST /api/v1/simulations/{id}/run
    API->>Engine: run_simulation(simulation_id)
    Engine->>Engine: assert_simulation_safety("COMPUTE_SCENARIO_OUTCOMES")
    Engine->>Engine: Compute Revenue, Burn, Headcount, Variance
    Engine->>Repo: save_simulation_result()
    Engine->>Repo: save_simulation_financial_record()
    Engine-->>API: Return SimulationResult
    API-->>User: 200 OK (Simulated Metrics & Deliberation)
```

---

## 9. Security Verification & Middleware Flowchart

```mermaid
flowchart TD
    Req[Incoming HTTP Request] --> Extract[Extract X-Company-ID & X-Environment-ID]
    Extract --> HasHeader{Company Header Present?}
    HasHeader -- Yes --> SetCtx[Inject CompanyContext into Request State]
    HasHeader -- No --> DefaultCtx[Inject Default Company Context]
    SetCtx --> Route[Route Handler Execution]
    DefaultCtx --> Route
    Route --> AccessCheck{Verify Target Resource Company ID == Context Company ID?}
    AccessCheck -- Match --> Success[Allow Execution]
    AccessCheck -- Mismatch --> Reject[Raise TenantIsolationViolationError / 403 Forbidden]
```

---

## 10. End-to-End Simulation Pipeline Flowchart

```mermaid
flowchart TD
    Start([Start What-If Simulation]) --> SelectSnapshot[Select Baseline Snapshot]
    SelectSnapshot --> DefineVariables[Define Staffing / Pricing / Marketing Variables]
    DefineVariables --> InitSim[Initialize CompanySimulation Object]
    InitSim --> AssertSafety{Assert Environment == SIMULATION & Action Safe?}
    AssertSafety -- Safe --> RunEngine[Run Scenario Calculation Engine]
    AssertSafety -- Unsafe --> RaiseErr[Raise SimulationProductionMutationError]
    RunEngine --> ComputeMetrics[Compute Simulated Revenue, Burn, Headcount, Runway]
    ComputeMetrics --> ComputeVariance[Compute Delta % and Variance Analytics]
    ComputeVariance --> SaveRecord[Save Isolated Simulation Financial Record]
    SaveRecord --> SaveResult[Save Simulation Result & Complete Run]
    SaveResult --> RenderUI[Render Side-by-Side Comparison in Pixel Office UI]
    RenderUI --> End([Simulation Complete])
```

---

## 11. REST API Endpoints Reference

### Multi-Company Endpoints (`/api/v1/companies`)
- `GET /api/v1/companies` — List all managed companies.
- `POST /api/v1/companies` — Provision new autonomous company.
- `GET /api/v1/companies/{id}` — Get company details.
- `POST /api/v1/companies/{id}/lifecycle` — Transition company lifecycle state.
- `GET /api/v1/companies/{id}/quota` — Get company resource quota utilization.
- `POST /api/v1/companies/relationships` — Create company relationship.
- `POST /api/v1/companies/data-shares` — Request cross-company data sharing.
- `POST /api/v1/companies/data-shares/{id}/approve` — Approve data share request.

### Simulation Endpoints (`/api/v1/simulations`)
- `POST /api/v1/simulations/snapshots` — Create baseline point-in-time snapshot.
- `POST /api/v1/simulations/scenarios` — Build what-if simulation scenario.
- `POST /api/v1/simulations` — Create simulation run instance.
- `POST /api/v1/simulations/{id}/run` — Execute scenario calculation engine.
- `GET /api/v1/simulations/{id}/result` — Get simulation outcome comparison.

---

## 12. Verification & Safety Verification

All 19 Phase 25 tests pass clean:
- `test_company_domain.py` (4 passed)
- `test_company_repository.py` (3 passed)
- `test_company_services.py` (3 passed)
- `test_simulation_services.py` (2 passed)
- `test_company_routes.py` (3 passed)
- `test_multi_company_security_isolation.py` (2 passed)
- `test_simulation_safety_isolation.py` (2 passed)
