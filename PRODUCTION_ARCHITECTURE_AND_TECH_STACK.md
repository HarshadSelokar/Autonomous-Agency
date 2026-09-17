# Autonomous Company Platform 1.0
## Production Requirements, Technical Architecture & Complete Tech Stack

---

## 1. Executive Summary & System Vision

The **Autonomous Company Platform 1.0** is an enterprise-grade, end-to-end Operating System (OS) for running autonomous AI companies, ventures, and multi-tenant enterprise federations. Built across **31 progressive architectural phases**, the platform unifies agent execution, multi-agent collaboration, deterministic governance, strategic intelligence, continuous organizational learning, venture generation, production hardening, and enterprise disaster recovery into a single coherent control plane.

### Core System Philosophy & Invariants

```
HUMAN AUTHORIZATION > DETERMINISTIC GOVERNANCE > VERIFIED EVIDENCE > LLM REASONING
SECURITY + RELIABILITY + OBSERVABILITY + RECOVERABILITY + DATA INTEGRITY + GOVERNANCE + FAULT ISOLATION + AUDITABILITY
CLAIM != EVIDENCE != VERIFICATION != COMPLETION
THE SYSTEM MUST NEVER TRADE SAFETY FOR AUTONOMY.
SAFE DEGRADATION OVER UNCONTROLLED EXECUTION.
```

---

## 2. Production Requirements & Operational Standards

The platform is designed and validated to run in production under strict operational standards, handling hardware failures, network partitions, adversarial model outputs, high concurrency, and disaster recovery scenarios.

### 2.1 Availability & Resilience Requirements
* **High Availability (HA)**: Active-Active API tier behind load balancers with stateless HTTP handlers.
* **Degradation SLA**: The platform evaluates system health across three states (`NORMAL`, `DEGRADED`, `UNAVAILABLE`). Under single-dependency failure (e.g., LLM router outage), the platform gracefully degrades to cached reasoning/fallback policies without taking down core governance or task queues.
* **Circuit Breakers**: Dependencies wrapped in automated state machines (`CLOSED`, `OPEN`, `HALF_OPEN`) with threshold-based tripping (default 3 consecutive failures) and recovery probing timeouts (1.0s+ backoff).
* **Exponential Backoff & Full Jitter**: Automated retries on transient errors using full jitter distributions to avoid thundering herd conditions on external APIs.

### 2.2 Disaster Recovery (DR) & Business Continuity SLAs
* **Recovery Point Objective (RPO)**: **< 5 minutes**. Automated cryptographically signed backup snapshots capture point-in-time PostgreSQL database state, Redis state, and MinIO object artifacts.
* **Recovery Time Objective (RTO)**: **< 15 minutes**. Automated state reconciliation simulators verify fallback region startup (e.g., `EU_WEST_DISASTER_RECOVERY`) and component failover.
* **Backup Integrity Verification**: All snapshots undergo SHA-256 checksum comparison before certification for restoration.

### 2.3 Security & Compliance Requirements
* **Human Authorization Primacy**: Irreversible actions (financial disbursements, system deployment, policy alterations, high-risk venture capitalization) strictly require explicit human approval via governance proposal workflows.
* **Prompt Injection Defense**: Multi-layered guardrails (`SecurityIncidentEngine`) intercepting adversarial input vectors (`ignore previous instructions`, `system prompt override`, `jailbreak`, `credential extraction`) before LLM ingestion. Raises `SecurityBoundaryViolationError` and auto-triages security incidents.
* **Secret Masking & Redaction**: Zero-trust log & response filters redact sensitive tokens (`gsk_*`, `sk-*`, `ghp_*`, `eyJ*`, passwords, database credentials) with `[REDACTED]`.
* **Cryptographic Audit Trail**: Immutable append-only audit trail logging with parent SHA-256 hash chaining (`DataIntegrityEngine`). Any record tampering immediately invalidates the chain verification.
* **Multi-Tenant Data Isolation**: Row-Level and Tenant Foreign-Key scoping across all DB tables (`company_id`, `enterprise_id`), preventing cross-tenant data leaks.
* **Fast-Fail Production Startup**: `validate_production_env()` prevents application launch if `APP_ENV=production` is paired with `DEBUG=True`, default/placeholder credentials (`postgres:postgres`, `minioadmin`), or local SQLite fallbacks.

### 2.4 Performance & Scalability Requirements
* **Connection Pooling**:
  * PostgreSQL: Pool size `20` + max overflow `10`, recycle after `1800s`.
  * Redis Async Pool: Max `50` concurrent connections.
* **Payload Limits**: `RequestSizeLimitMiddleware` rejects payloads `> 10 MB` with `HTTP 413 Payload Too Large`.
* **Worker Queue Bounds**: Async worker pools enforce drain timeouts (`30.0s`) and token budget caps per execution step.

---

## 3. Complete Technical Stack Specification

```
+-----------------------------------------------------------------------------------+
|                               PIXEL OFFICE FRONTEND                               |
|              React 18 | TypeScript 5.3 | Vite 5.4 | TailwindCSS v4               |
+-----------------------------------------------------------------------------------+
                                          | HTTP / WebSockets
                                          v
+-----------------------------------------------------------------------------------+
|                              FASTAPI API GATEWAY 1.0                              |
|           FastAPI 0.110 | Uvicorn 0.28 | Pydantic v2.6 | AsyncIO               |
|            Resilience & Security Middleware | CORS | OpenAPI / Swagger            |
+-----------------------------------------------------------------------------------+
       |                                  |                                  |
       v                                  v                                  v
+------------------+            +-------------------+              +------------------+
| PLATFORM CONTROL |            |  CORE ENGINES     |              | RESILIENCE & DR  |
|  PLANE & VIEWS   |            | Intelligence      |              | Circuit Breakers |
| Executive        |            | Org Learning      |              | Audit Hash Chains|
| Manager          |            | Venture Creation  |              | Guardrail Filter |
| Employee         |            | Swarm Execution   |              | DR Snapshot Sync |
+------------------+            +-------------------+              +------------------+
       |                                  |                                  |
       +----------------------------------+----------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                               PERSISTENCE & STORAGE                               |
|  PostgreSQL 15 (AsyncPG + SQLAlchemy 2.0) | Redis 7.0 (Queue & Cache)            |
|  Alembic Migrations (001-029)             | MinIO / AWS S3 (Artifact Store)      |
+-----------------------------------------------------------------------------------+
```

### 3.1 Backend Architecture Stack
* **Core Language & Runtime**: Python 3.11+
* **Web Framework**: FastAPI `0.110.0+`
* **ASGI Server**: Uvicorn `0.28.0+` (standard with `uvloop` & `httptools`)
* **Data Validation & Settings**: Pydantic `2.6.0+`, Pydantic-Settings `2.2.0+`
* **HTTP Client Engine**: HTTPX `0.27.0+` (async client with connection pooling)

### 3.2 Data & Storage Stack
* **Relational Database**: PostgreSQL 15 (Alpine)
* **Async Database Driver**: AsyncPG `0.29.0+`
* **Object-Relational Mapping (ORM)**: SQLAlchemy `2.0.28+` (Async Engine & AsyncSession)
* **Database Migrations**: Alembic `1.13.0+` (29 structured migrations from core agent tables to Phase 30 resilience schema)
* **Local Test Database**: SQLite via AIOSQLite `0.20.0+` (isolated fast test runner)
* **In-Memory Cache & Message Broker**: Redis 7.0 (Alpine) via Redis-Py `5.0.0+`
* **Object / Artifact Storage**: MinIO / AWS S3 (S3 API compatible artifact & document storage)

### 3.3 AI, LLM & Orchestration Engine Stack
* **LLM Provider Integration**: Groq API SDK (`groq>=0.5.0`) with model routing & fallback chains
* **Model Router**: Dynamic latency/cost-optimized provider routing with local cache fallback
* **Token Budget Manager**: Phase 19 token cap enforcer & cost control accounting

### 3.4 Frontend Architecture Stack (Pixel Office)
* **UI Framework**: React 18.2.0
* **Language**: TypeScript 5.3.3
* **Build Tooling & Bundler**: Vite 5.4.21 with `@vitejs/plugin-react`
* **Styling Engine**: TailwindCSS 4.3.3 (`@tailwindcss/vite`) + Custom Glassmorphic Dark Tokens
* **Iconography**: Lucide React `0.344.0`
* **Component Dashboards**:
  * Platform Control Center (`PlatformControlCenterDashboard.tsx`) — Executive, Manager, Employee, Workflows
  * Resilience & DR Control (`ResilienceDashboard.tsx`) — Circuit Breakers, Threats, Audit Chain, DR
  * Enterprise OS Dashboard (`EnterpriseDashboard.tsx`) — Federation, Governance, Multi-Company
  * Company Intelligence Dashboard (`CompanyIntelligenceDashboard.tsx`) — Health, Bottlenecks, Simulation
  * Continuous Learning Dashboard (`LearningDashboard.tsx`) — Adaptations, Proposals
  * Autonomous Venture Dashboard (`VentureDashboard.tsx`) — Spinoffs, Capitalization

### 3.5 Development, Quality & Testing Stack
* **Test Runner**: Pytest `8.0.0+`, Pytest-Asyncio `0.23.0+`, Pytest-Cov `4.1.0+`
* **Linter & Formatter**: Ruff `0.3.0+` (Python 3.11 target, line length 100)
* **Static Type Checker**: MyPy `1.9.0+` (Strict typing mode enabled)
* **Containerization**: Docker, Docker Compose (`3.8`), Multi-stage `Dockerfile` and `Dockerfile.worker`

---

## 4. Comprehensive Layered Architecture (Phases 1–31)

The platform is structured into **7 interconnected functional layers**:

```
+-----------------------------------------------------------------------------------+
| LAYER 1: UNIFIED PLATFORM CONTROL PLANE                                            |
| PlatformControlPlane | PlatformWorkflowEngine | System Health & Readiness Matrix |
+-----------------------------------------------------------------------------------+
| LAYER 2: API & GATEWAY LAYER                                                      |
| FastAPI Routers | Platform Views (Exec/Mgr/Emp) | Search API | Onboarding | WS Engine |
+-----------------------------------------------------------------------------------+
| LAYER 3: ENTERPRISE & FEDERATION LAYER                                            |
| Multi-Company Isolation | Enterprise Federation | Sandbox Simulation | Venture Engine |
+-----------------------------------------------------------------------------------+
| LAYER 4: INTELLIGENCE & LEARNING LAYER                                            |
| Company Intelligence | Bottleneck Discovery | Governed Adaptation | Org Memory |
+-----------------------------------------------------------------------------------+
| LAYER 5: RESILIENCE, SECURITY & GOVERNANCE LAYER                                  |
| Circuit Breakers | Security Incident Engine | SHA-256 Audit Chain | Disaster Recovery|
+-----------------------------------------------------------------------------------+
| LAYER 6: AGENT RUNTIME & EXECUTION SWARM                                          |
| Memory | Tool Sandbox | Planning | Swarm Orchestration | Model Router | Token Budget  |
+-----------------------------------------------------------------------------------+
| LAYER 7: INFRASTRUCTURE & DATA PERSISTENCE                                        |
| PostgreSQL | AsyncPG | SQLAlchemy ORM | Redis | MinIO/S3 | Alembic Migrations |
+-----------------------------------------------------------------------------------+
```

### Layer 1: Unified Platform Control Plane (Phase 31)
* **`PlatformControlPlane`**: Orchestrates company & enterprise readiness checks (`CompanyReadinessCheck`, `EnterpriseReadinessCheck`) and manages system-wide lifecycle states (`INITIALIZING`, `BOOTSTRAPPED`, `ACTIVE`, `DEGRADED`, `SUSPENDED`, `ARCHIVED`).
* **`PlatformWorkflowEngine`**: Executes cross-phase workflows with context passing, multi-step state tracking, and rollback handlers.

### Layer 2: API & Gateway Layer (Phases 20 & 31)
* **Role-Tailored Views**: Serves tailored aggregated views for `/views/executive`, `/views/manager`, and `/views/employee`.
* **Unified Search Endpoint**: Single `/search` route performing cross-domain queries over companies, ventures, workflows, security incidents, and intelligence metrics.
* **Onboarding Router**: Interactive guided onboarding pipeline creating bootstrap companies and initial agent teams.

### Layer 3: Enterprise & Federation Layer (Phases 25, 28 & 29)
* **Multi-Company Data Isolation**: Strict tenant scoping across all domain entities.
* **What-If Simulation Sandbox**: Sandboxed scenario simulation engine evaluating organizational changes prior to live execution.
* **Autonomous Venture Creation**: Evaluates innovation ideas, generates venture proposals, and manages spinoff capitalization.
* **Enterprise Federation OS**: Governs cross-company data sharing contracts, enterprise resource distribution, and parent-subsidiary alignment.

### Layer 4: Intelligence & Learning Layer (Phases 26 & 27)
* **Advanced Company Intelligence**: Synthesizes multi-dimensional health metrics across operational, financial, and strategic domain vectors.
* **Bottleneck Discovery Engine**: Identifies structural agent delays and resource constraints automatically.
* **Continuous Organizational Learning**: Converts operational feedback into governed adaptation proposals.

### Layer 5: Resilience, Security & Governance Layer (Phases 7, 10, 16 & 30)
* **Resilience Engine**: Manages dependency circuit breakers (`CLOSED`/`OPEN`/`HALF_OPEN`), jitter backoff, and system degradation levels.
* **Security Incident Engine**: Guardrail scanner filtering prompt injections and masking sensitive credentials.
* **Data Integrity Engine**: Generates SHA-256 hash chains for tamper-evident audit logs.
* **Disaster Recovery Engine**: Snapshot validation, RPO/RTO compliance verification, and regional failover reconciliation.

### Layer 6: Agent Runtime & Swarm Execution (Phases 1–19, 24)
* **Agent Runtime & Memory**: Short-term context frames, long-term episodic reflection memory.
* **Tool System & Execution Engine**: Sandboxed tool invocation with safety policy checks.
* **Multi-Agent Collaboration**: Orchestrates agent swarms, role assignments, and inter-agent dialogues.
* **Scalable Worker Pool**: Queue-based task distribution via Redis worker processes.

### Layer 7: Infrastructure & Data Persistence (Phases 15, 20 & 30)
* **PostgreSQL Schema**: 29 Alembic migrations managing 40+ relational tables.
* **Redis Store**: Caching runtime states, task queues, and rate-limiting counters.
* **MinIO Object Store**: S3-compatible artifact storage for snapshots and generated documents.

---

## 5. Deployment Topology & Production Environment

### 5.1 Docker Compose Production Service Topology

```yaml
services:
  postgres:
    image: postgres:15-alpine
    healthcheck: pg_isready -U postgres -d agent_runtime
    volumes: [ postgres_data ]

  redis:
    image: redis:7-alpine
    healthcheck: redis-cli ping
    volumes: [ redis_data ]

  minio:
    image: minio/minio
    healthcheck: http://localhost:9000/minio/health/live
    volumes: [ minio_data ]

  api:
    build: Dockerfile (FastAPI + Uvicorn)
    ports: ["8000:8000"]
    depends_on: [ postgres, redis, minio ]

  worker:
    build: Dockerfile.worker (Background Execution Pool)
    depends_on: [ postgres, redis, minio ]
```

### 5.2 Environment Variables & Config (`.env`)

| Variable | Description | Production Example |
|---|---|---|
| `APP_ENV` | Application environment mode | `production` |
| `DATABASE_URL` | PostgreSQL connection URI | `postgresql+asyncpg://user:pass@db:5432/agent_runtime` |
| `REDIS_URL` | Redis connection URI | `redis://redis:6379/0` |
| `STORAGE_TYPE` | Object storage mode | `s3` |
| `S3_ENDPOINT_URL` | MinIO / AWS S3 endpoint | `http://minio:9000` |
| `S3_BUCKET_NAME` | Artifact bucket | `autonomous-artifacts` |
| `GROQ_API_KEY` | Groq LLM API Key | `gsk_...` |
| `DEBUG` | FastAPI debug mode | `False` |

---

## 6. Verification & Test Suite Summary

The entire architecture is verified by a 76-test automated regression suite and full E2E demonstration scripts:

- **Unit & Integration Suite**: `76/76 passed cleanly` (`pytest`)
- **Frontend TS/Vite Build**: `0 errors` (`npm run build`)
- **31-Step Golden Path**: `100% successful execution` (`scripts/demo_platform_1_0.py`)
- **Release Checklist Certification**: `20/20 criteria passed` (`docs/release/platform_1_0_release_checklist.md`)

---

*Certified for Production Release — Autonomous Company Platform 1.0*
