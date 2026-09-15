# Phase 12 — Model Routing & Intelligent Model Selection Architecture

## Overview

Model Routing provides a provider-neutral optimization layer for selecting the optimal Large Language Model (LLM) for agent tasks while ensuring strict compliance with governance policy allowlists/blocklists, operational health, quality targets, and budget boundaries.

```
ModelSelectionRequest
        ↓
1. Governance Filter (Allowlist / Blocklist / Approval)
        ↓
2. Capability & Health Filter
        ↓
3. Strategy Scoring (Quality / Cost / Latency / Health)
        ↓
ModelSelectionDecision (Explainable)
```

---

## Domain Concepts

### 1. Model Profiles & Provider Independence (`src/domain/model_routing.py`)
Model profiles capture capabilities (`TEXT_GENERATION`, `CODE_GENERATION`, `REASONING`, `VISION`, etc.), token window sizes, input/output cost per 1k tokens, latency (ms), quality scores, and production approval status.
Supported providers are pluggable adapters (`Groq`, `Fake`, `OpenAI`, etc.).

### 2. Routing Strategies
- `RULE_BASED`: Uses explicit model assignment.
- `CAPABILITY_BASED`: Selects highest capability match.
- `QUALITY_AWARE`: Maximizes quality score.
- `COST_AWARE`: Minimizes token cost while satisfying capability constraints.
- `LATENCY_AWARE`: Minimizes response time.
- `HEALTH_AWARE`: Penalizes providers experiencing errors or degradation.

### 3. Health Monitoring & Provider Outage Fallback
`ModelRouter` dynamically tracks provider health signals (`is_healthy`, `error_rate`, `latency_p95_ms`). Unhealthy models are filtered out during candidate selection. If all primary candidates are degraded, controlled fallback is activated with full audit logging.

### 4. Explainable Selection Decisions
Every routing decision generates a persistent `ModelSelectionDecision` containing score breakdowns, candidate evaluation logs, rejected candidate reasons, and fallback flags.

---

## Technical Components

- **Domain Model**: [`src/domain/model_routing.py`](file:///d:/agency/src/domain/model_routing.py)
- **Application Service**: [`src/application/model_router.py`](file:///d:/agency/src/application/model_router.py)
- **Persistence Layer**: [`src/infrastructure/models/model_routing_model.py`](file:///d:/agency/src/infrastructure/models/model_routing_model.py) & [`src/infrastructure/repositories/model_routing_repository.py`](file:///d:/agency/src/infrastructure/repositories/model_routing_repository.py)
- **REST API**: [`src/api/routes/model_routing.py`](file:///d:/agency/src/api/routes/model_routing.py)
