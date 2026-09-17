# Phase 26 — Advanced Company Intelligence, Decision Support & Strategic Optimization

## Architectural Vision & Core Invariants

Phase 26 introduces the **Company Intelligence & Decision Support System** for the Autonomous AI Organization Platform. It serves as the institutional brain that synthesizes operational telemetry into high-confidence insights, formulates multi-option strategic decision spaces, enforces human governance boundaries, and continuously learns from post-execution outcomes.

### Core Architectural Invariants
1. **Intelligence Invariant Pipeline**:
   $$\text{FACT} \neq \text{OBSERVATION} \neq \text{FORECAST} \neq \text{PREDICTION} \neq \text{SCENARIO} \neq \text{REALITY}$$
2. **Recommendation vs. Decision Separation**:
   $$\text{RECOMMENDATION} \neq \text{DECISION}$$
3. **Governed Decision Execution Flow**:
   $$\text{APPROVED DECISION} \neq \text{EXECUTION} \neq \text{VERIFICATION} \neq \text{OUTCOME} \neq \text{LEARNING}$$
4. **Operational Non-Mutation**: The Intelligence & Decision Support Layer is strictly advisory; it NEVER directly mutates operational state without going through governed execution bridges with valid `governance_approval_id` tokens.
5. **Status-Quo Baseline Requirement**: Every strategic evaluation MUST automatically inject and evaluate Option 0 (`NO_ACTION` maintain status quo) as a comparative baseline.

---

## System Architecture & Sequence Diagrams

### 1. Overall System Architecture Layering

```mermaid
graph TD
    subgraph Operational Domain Layer
        TE[Task Engine]
        WF[Workforce Allocation]
        FIN[Financial Ledger]
        CRM[Customer & Sales CRM]
        PRD[Product Engineering]
    end

    subgraph Data Isolation Boundary
        MT[Multi-Tenant Context Scope]
    end

    subgraph Company Intelligence & Decision Layer
        IR[Intelligence Run Engine]
        HA[Health Synthesis Engine]
        BD[Bottleneck Discovery]
        RA[Risk & Opportunity Evaluator]
        DS[Decision Support Engine]
        EB[Governance Execution Bridge]
        OL[Outcome Learning Loop]
    end

    subgraph Human Governance Boundary
        GOV[Governance Control Panel / Chairman]
    end

    TE -->|Telemetry & Metrics| IR
    WF -->|Capacity Telemetry| IR
    FIN -->|Burn & Revenue| IR
    CRM -->|Sales Velocity| IR
    PRD -->|Roadmap Progress| IR

    IR --> HA
    IR --> BD
    IR --> RA
    HA --> DS
    BD --> DS

    DS -->|Formulates Insights & Options| GOV
    GOV -->|Attaches governance_approval_id| EB
    EB -->|Governed Action Payload| TE
    EB -->|Governed Action Payload| WF

    TE -->|Post-Execution Results| OL
    OL -->|Counterfactual Learnings| DS
```

---

### 2. Intelligence Invariant State Machine

```mermaid
stateDiagram-v2
    [*] --> FACT : Raw Event Telemetry
    FACT --> OBSERVATION : Analytical Pattern Detection
    OBSERVATION --> FORECAST : Time-Series Trend Extrapolation
    FORECAST --> PREDICTION : Predictive Machine Learning
    PREDICTION --> SCENARIO : What-If Simulation Modeling
    SCENARIO --> RECOMMENDATION : Multi-Dimensional Scoring
    RECOMMENDATION --> APPROVED_DECISION : Human Governance Approval (id)
    APPROVED_DECISION --> EXECUTION : Governed Bridge Dispatch
    EXECUTION --> REALITY : Post-Execution Telemetry
    REALITY --> LEARNING : Counterfactual Variance Analysis
    LEARNING --> [*]
```

---

### 3. Multi-Dimensional Company Health Synthesis Engine

```mermaid
flowchart LR
    subgraph Dimensions [10 Domain Dimensions]
        D1[Strategic]
        D2[Financial]
        D3[Product]
        D4[Customer]
        D5[GTM & Sales]
        D6[Workforce]
        D7[Engineering]
        D8[Operations]
        D9[Reliability]
        D10[Governance]
    end

    subgraph Engine [Health Assessment Synthesizer]
        SCORE[Weighted Score Aggregator]
        STATUS[Status Categorizer: HEALTHY | BALANCED | AT_RISK | CRITICAL]
        SYNTH[Risk & Opportunity Extractor]
    end

    D1 & D2 & D3 & D4 & D5 & D6 & D7 & D8 & D9 & D10 --> SCORE
    SCORE --> STATUS
    SCORE --> SYNTH
    STATUS --> AssessmentResult[CompanyHealthAssessment Artifact]
    SYNTH --> AssessmentResult
```

---

### 4. Operational Bottleneck & Root-Cause Discovery Flow

```mermaid
sequenceDiagram
    autonumber
    participant Engine as Intelligence Engine
    participant Repo as Company Intelligence Repo
    participant Telemetry as Operational Telemetry
    participant Analyzer as Root-Cause Analyzer

    Engine->>Telemetry: Query Task Backlog, Queue Velocity & Utilization
    Telemetry-->>Engine: Task Queue Delay +35%, Utilization 92%
    Engine->>Analyzer: Trace Contention Graph & Task Dependencies
    Analyzer-->>Engine: Pinpoint Senior Backend Engineer Shortage
    Engine->>Repo: Save CompanyBottleneck(HIGH, SOFTWARE_DEVELOPMENT)
    Repo-->>Engine: Bottleneck Saved
```

---

### 5. Multi-Option Decision Space Generator

```mermaid
flowchart TD
    Q[Strategic Question Input] --> CheckBaseline{Contains Status-Quo Baseline?}
    CheckBaseline -- No --> Inject[Auto-Inject Option 0: Maintain Status Quo]
    CheckBaseline -- Yes --> Alternatives[Parse Strategic Alternatives]
    Inject --> OptionsList[Consolidated Option Set]
    Alternatives --> OptionsList
    OptionsList --> Opt0[Option 0: Status-Quo Baseline]
    OptionsList --> Opt1[Option 1: Primary Strategic Action]
    OptionsList --> OptN[Option N: Alternative Action]
```

---

### 6. Multi-Dimensional Option Evaluator & Strategic Trade-off Analyzer

```mermaid
graph LR
    subgraph Decision Options
        O0[Option 0: Baseline]
        O1[Option 1: Expand Capacity]
    end

    subgraph Multi-Dimensional Evaluator
        S1[Strategic Alignment Score]
        S2[Financial Impact Score]
        S3[Customer Impact Score]
        S4[Product Impact Score]
        S5[Workforce Impact Score]
        S6[Operational Risk Score]
        S7[Execution Complexity Score]
        S8[Reversibility Score]
    end

    subgraph Trade-off Synthesis
        TO[Strategic Trade-off Matrix]
        INS[Decision Insight Brief]
    end

    O0 & O1 --> S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8
    S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8 --> TO
    TO --> INS
```

---

### 7. Governance Boundary & Execution Bridge Checkpoint

```mermaid
flowchart TD
    Insight[Decision Insight Created] --> CheckGov{governance_approval_id Present?}
    CheckGov -- No --> Block[THROW UnauthorizedDecisionExecutionError: HTTP 403]
    CheckGov -- Yes --> VerifyExpiry{Is Insight Expired?}
    VerifyExpiry -- Yes --> Reject[THROW DecisionInsightExpiredError: HTTP 400]
    VerifyExpiry -- No --> Execute[Bridge Execution Payload to Task Engine]
    Execute --> State[Mark Insight is_executed = True]
```

---

### 8. Post-Execution Outcome Evaluation & Counterfactual Learning Loop

```mermaid
sequenceDiagram
    autonumber
    participant Exec as Governed Execution
    participant Eval as Decision Outcome Learning Service
    participant Repo as Intelligence Repository
    participant KI as Institutional Knowledge Base

    Exec->>Eval: Submit Actual Post-Execution Outcomes
    Eval->>Eval: Compute Variance (Actual vs Expected vs Counterfactual Baseline)
    Eval->>Repo: Save DecisionOutcomeEvaluation Record
    Eval->>KI: Register Validated Learning Candidate as Knowledge Item
    KI-->>Eval: KI ID Generated (ki-lesson-xxx)
```

---

### 9. Multi-Tenant Intelligence Isolation Model

```mermaid
graph TB
    subgraph Request Context
        ReqA[API Request: Tenant A]
        ReqB[API Request: Tenant B]
    end

    subgraph Repository Guard Layer
        Guard[SQLAlchemy Tenant Scope Enforcer]
    end

    subgraph Isolated Storage
        DBA[(Company A Intelligence Tables)]
        DBB[(Company B Intelligence Tables)]
    end

    ReqA --> Guard
    ReqB --> Guard
    Guard -->|Filter company_id == 'comp-A'| DBA
    Guard -->|Filter company_id == 'comp-B'| DBB
    Guard -.->|BLOCK Cross-Tenant Access| Error[HTTP 404 / 403 Forbidden]
```

---

### 10. Pixel Office Company Intelligence Dashboard Architecture

```mermaid
graph TD
    subgraph UI Layout
        Nav[Sidebar Navigation Link: Company Intelligence]
        App[App Shell & Router]
    end

    subgraph Dashboard Tabs
        T1[Tab 1: Strategic Health Radar]
        T2[Tab 2: Bottleneck & Root-Cause Explorer]
        T3[Tab 3: Strategic Decision Evaluator]
        T4[Tab 4: Outcome & Learning Feed]
    end

    subgraph Client State & API
        State[React Active Tab & State]
        API[apiClient REST Interface]
    end

    Nav --> App
    App --> T1 & T2 & T3 & T4
    T1 & T2 & T3 & T4 --> State
    State --> API
```

---

## Summary of REST API Endpoints

| Method | Endpoint Path | Description |
|---|---|---|
| `POST` | `/api/v1/intelligence/companies/{company_id}/runs` | Start & execute an analytical intelligence run |
| `GET` | `/api/v1/intelligence/companies/{company_id}/runs/{run_id}` | Retrieve intelligence run findings & uncertainty score |
| `GET` | `/api/v1/intelligence/companies/{company_id}/runs` | List historical intelligence runs for company |
| `GET` | `/api/v1/intelligence/companies/{company_id}/health` | Fetch multi-dimensional health assessment |
| `GET` | `/api/v1/intelligence/companies/{company_id}/bottlenecks` | List detected operational bottlenecks & root-causes |
| `GET` | `/api/v1/intelligence/companies/{company_id}/risks` | Fetch categorized risk assessments |
| `POST` | `/api/v1/intelligence/companies/{company_id}/decision-questions` | Submit a first-class decision query |
| `POST` | `/api/v1/intelligence/companies/{company_id}/decision-questions/{question_id}/evaluate` | Formulate options (with baseline), evaluate & synthesize insight |
| `GET` | `/api/v1/intelligence/companies/{company_id}/decision-insights/{insight_id}` | Fetch decision insight brief |
| `POST` | `/api/v1/intelligence/companies/{company_id}/decision-insights/{insight_id}/execute` | Bridge decision to execution workflow (requires `governance_approval_id`) |
| `POST` | `/api/v1/intelligence/companies/{company_id}/decision-outcomes/evaluate` | Post-execution outcome variance tracking & counterfactual learning |
