# Phase 18 — Autonomous Knowledge, Organizational Memory & Institutional Learning

## Executive Overview

Phase 18 expands the platform's foundational Phase 7 Memory System into an **Institutional Knowledge & Organizational Learning Framework**. It enables the autonomous AI organization to systematically convert raw task executions, observations, and telemetry into verified evidence, candidate knowledge items, authoritative institutional memory, versioned operating procedures, and isolated organizational experiments.

## Architectural Flow & Principles

```mermaid
flowchart TD
    RawInfo["RAW INFORMATION & OBSERVATION"] --> Evidence["DETERMINISTIC EVIDENCE & TELEMETRY"]
    Evidence --> Candidate["KNOWLEDGE CANDIDATE (UNVERIFIED)"]
    Candidate --> Validation["INDEPENDENT EVIDENCE VALIDATION"]
    Validation -->|Failed / LLM Only| Invalidated["INVALIDATED / REJECTED"]
    Validation -->|Passed (Non-LLM Evidence)| Validated["VALIDATED KNOWLEDGE"]
    Validated --> ConflictCheck["CONFLICT DETECTION & RESOLUTION"]
    ConflictCheck -->|Conflict Resolved| Superseded["SUPERSEDED KNOWLEDGE"]
    ConflictCheck -->|Confirmed| Authoritative["AUTHORITATIVE KNOWLEDGE / POLICY"]
    Authoritative --> Procedure["VERSIONED PROCEDURES (SOP)"]
    Procedure --> Phase11["PHASE 11 GOVERNANCE APPROVAL"]
    Authoritative --> Experiment["ISOLATED ORGANIZATIONAL EXPERIMENTS"]
    Experiment --> Candidate
```

### Core Invariants Enforced

1. **MEMORY != KNOWLEDGE**: Transient episodic/semantic memories do not directly alter institutional policy.
2. **KNOWLEDGE CANDIDATE != VALIDATED KNOWLEDGE**: Unverified knowledge candidates require independent deterministic validation before promotion.
3. **VALIDATED KNOWLEDGE != POLICY**: Validated knowledge requires Phase 11 Human Governance authorization to become binding organizational policy.
4. **LLM OUTPUT != ORGANIZATIONAL TRUTH**: Multiple LLM string outputs do **NOT** count as independent evidence. Evidence must be backed by system telemetry, test runs, or deterministic verification log IDs.
5. **EXPERIMENT ISOLATION INVARIANT**: Every `OrganizationalExperiment` must be strictly isolated (`is_isolated = True`). High/Critical risk experiments require explicit Phase 11 Governance authorization before activation.

## Key Components Implemented

| Layer | Module / File | Description |
| :--- | :--- | :--- |
| **Domain** | [`src/domain/knowledge.py`](file:///d:/agency/src/domain/knowledge.py) | Entities: `KnowledgeItem`, `KnowledgeClaim`, `KnowledgeProvenance`, `KnowledgeValidation`, `KnowledgeConflict`, `KnowledgeRelationship`, `KnowledgeProcedure`, `KnowledgeUsageRecord`. Enums: `KnowledgeAuthority`, `KnowledgeStatus`, `KnowledgeType`, `KnowledgeScope`, `ConflictStatus`. |
| **Domain** | [`src/domain/experiment.py`](file:///d:/agency/src/domain/experiment.py) | Entity: `OrganizationalExperiment` (`is_isolated = True` invariant enforced). Enum: `ExperimentStatus`. |
| **Persistence** | [`src/infrastructure/models/knowledge_model.py`](file:///d:/agency/src/infrastructure/models/knowledge_model.py) | SQLAlchemy ORM models for all Phase 18 knowledge and experiment tables. |
| **Persistence** | [`migrations/versions/019_create_phase18_institutional_knowledge_tables.py`](file:///d:/agency/migrations/versions/019_create_phase18_institutional_knowledge_tables.py) | Alembic DB migration script (`down_revision = '018'`). |
| **Repository** | [`src/infrastructure/repositories/knowledge_repository.py`](file:///d:/agency/src/infrastructure/repositories/knowledge_repository.py) | `SQLAlchemyKnowledgeRepository` for async persistence & retrieval. |
| **Application** | [`src/application/knowledge_validation_service.py`](file:///d:/agency/src/application/knowledge_validation_service.py) | Multi-stage candidate validation pipeline, independent evidence verification, conflict resolution, staleness decay calculation. |
| **Application** | [`src/application/institutional_learning_service.py`](file:///d:/agency/src/application/institutional_learning_service.py) | Learning engines: failure learning, success pattern extraction, forecast learning, decision/workforce/tool/model/strategy lessons. |
| **Application** | [`src/application/procedure_management_service.py`](file:///d:/agency/src/application/procedure_management_service.py) | Versioned procedure (SOP) management & Phase 11 governance authorization. |
| **Application** | [`src/application/organizational_experiment_service.py`](file:///d:/agency/src/application/organizational_experiment_service.py) | Isolated experiment lifecycle management and promotion to knowledge candidate. |
| **API** | [`src/api/routes/knowledge.py`](file:///d:/agency/src/api/routes/knowledge.py) & [`src/api/routes/experiments.py`](file:///d:/agency/src/api/routes/experiments.py) | FastAPI REST endpoints for knowledge, validation, procedures, conflicts, and experiments. |
| **Projection** | [`src/application/office_projection_service.py`](file:///d:/agency/src/application/office_projection_service.py) | Pixel Office real-time visualization of knowledge metrics (candidates, validated, authoritative, contested, stale, active experiments). |

## Verification & Validation

- **Unit & Integration Tests**: 100% pass rate across 502 tests.
- **Security Test Suite**: [`tests/security/test_knowledge_security.py`](file:///d:/agency/tests/security/test_knowledge_security.py) (verifies anti-poisoning, independent evidence, experiment isolation, and governance gating).
- **Failure Injection Suite**: [`tests/failure_injection/test_knowledge_failure_injection.py`](file:///d:/agency/tests/failure_injection/test_knowledge_failure_injection.py) (verifies candidate invalidation under negative evidence and staleness decay).
- **Concurrency Test Suite**: [`tests/concurrency/test_knowledge_concurrency.py`](file:///d:/agency/tests/concurrency/test_knowledge_concurrency.py) (verifies concurrent validation and procedure creation).
- **E2E Demonstration Script**: [`scripts/demo_institutional_learning_flow.py`](file:///d:/agency/scripts/demo_institutional_learning_flow.py).
