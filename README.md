# Autonomous AI Organization Platform

An autonomous enterprise runtime and multi-agent development studio built with **FastAPI**, **SQLAlchemy**, and a **React + Vite Pixel Office** simulation.

The platform includes the **Software Studio**: assign a goal and a git repository to an autonomous team of AI agents (Manager, Developers, QA, and Reviewer), and they will plan tickets, write code in parallel git worktrees, automatically install dependencies, execute test suites, review pull requests/diffs, and merge verified changes.

---

## Capabilities & Status

| Area | Status | Description |
| :--- | :--- | :--- |
| **Software Studio** | **Ready (End-to-End)** | Full lifecycle: planning, parallel worktrees, QA testing, code review, merge conflicts recovery, dependency installation. |
| **Pixel Office Dashboard** | **Active** | 2D pixel-art office animated live from backend events: desk work, meetings (planning, huddles, wrap-ups), and leisure breaks (table tennis, chess, chats). |
| **Engines** | **Dual Engine** | Runs via `loop` (Groq or OpenAI-compatible LLMs) or `agy` (headless Antigravity CLI with subscription models & zero API key requirement). |
| **Authentication** | **Enforced** | JWT Bearer authentication + `ADMIN_API_KEY` (`X-API-Key`). Configurable via `AUTH_REQUIRED`. |
| **Tenant Isolation** | **Enforced** | Database-level row multi-tenancy: every query, insert, update, and delete is automatically scoped to the authenticated tenant. |
| **Control Plane & Resilience** | **Phases 1–41** | Autonomous workflows (DAGs), circuit breakers, event bus outbox, verification engine, and audit trail logging. |
| **Database Support** | **Verified** | Alembic migrations `001`–`040` validated across PostgreSQL 15+ and SQLite (`sqlite+aiosqlite`). |

---

## Quick Start

### Prerequisites
* **Python**: 3.11+
* **Node.js**: 18+ and `npm`
* **Git**: Installed and available in PATH
* **Docker** *(Optional)*: For PostgreSQL, Redis, and MinIO services

---

### 1. Backend Setup

```bash
# 1. Install Python package with dev dependencies
pip install -e ".[dev]"

# 2. Create environment configuration
# On Linux / macOS / PowerShell:
cp .env.example .env
# On Windows cmd:
# copy .env.example .env
```

#### Configure `.env`
Edit `.env` with your settings:
* **LLM Provider**:
  * For Groq: `GROQ_API_KEY="gsk_..."` and `GROQ_MODEL="llama-3.3-70b-versatile"` (or supported model)
  * For OpenAI-compatible: `STUDIO_PROVIDER="openai"`, `OPENAI_API_KEY="sk_..."`, `OPENAI_MODEL="gpt-4o"`
  * For Antigravity CLI: `STUDIO_ENGINE="agy"` (uses local `agy` credentials; no API key needed)
* **Authentication**:
  * `ADMIN_API_KEY="your-admin-secret-key"`
  * `AUTH_SECRET_KEY="your-jwt-secret-key"`
  * Set `AUTH_REQUIRED=false` for quick local testing without login tokens
* **Database**:
  * Local SQLite: `DATABASE_URL="sqlite+aiosqlite:///agency.db"`
  * Or PostgreSQL: `DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/agent_runtime"`

#### Run Database Migrations & Start Server
```bash
# Run migrations to head
alembic upgrade head

# Start the FastAPI server on port 8000
uvicorn src.api.main:app --reload --port 8000
```

* **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 2. Frontend Setup (Pixel Office)

In a second terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

* **Pixel Office App**: [http://localhost:3000](http://localhost:3000) (automatically proxies `/api`, `/studio`, and WebSocket `/office/ws` to backend port `8000`)
* **Sign In**: Log in using your registered credentials, paste your `ADMIN_API_KEY`, or click directly through if `AUTH_REQUIRED=false`.
* **Legacy Dashboards**: [http://localhost:3000/#/legacy](http://localhost:3000/#/legacy)

---

### 3. Run with Docker Compose

To run PostgreSQL, Redis, MinIO, and the API backend inside containers:

```bash
# Start all infrastructure and backend services in background
docker compose up -d

# Check service logs
docker compose logs -f api

# Tear down services
docker compose down
```

---

## Software Studio

### Run via Command Line (No Database Required)

You can launch the autonomous software engineering team against any local git repository without starting the database:

```bash
python -m scripts.run_studio_project "Add a /version endpoint with a test" \
  --repo path/to/your/repo \
  --test "python -m pytest -q"
```

To run with the Antigravity headless engine instead of an API key:
```bash
python -m scripts.run_studio_project "Add a /version endpoint with a test" \
  --repo path/to/your/repo \
  --test "python -m pytest -q" \
  --engine agy
```

> [!NOTE]
> The repository is cloned into `scratch/studio/<project-id>`. The original directory is never modified. Changes and commits land on the `agency/<project-id>` branch inside that clone. Nothing is pushed to remotes.

---

### Studio Execution Lifecycle

```
       ┌────────────────────────┐
       │   Manager: Planning    │  (Breaks goal into tickets with dependencies)
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│ Developer A (ws) │  │ Developer B (ws) │  (Concurrent isolated worktrees)
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └─────────┬───────────┘
                   ▼
       ┌────────────────────────┐
       │  Auto-Install & Test   │  (Runs npm install / pip install, executes test command)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │    Reviewer Sign-Off   │  (Inspects diff, verifies quality, requests rework if needed)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │  Merge Gate / Human    │  (Replays on latest branch, checks conflicts, merges commit)
       └────────────────────────┘
```

1. **Manager**: Analyzes repository structure and splits the goal into dependency-ordered tickets.
2. **Developers**: Work on tickets concurrently in independent git worktrees (`STUDIO_DEVELOPERS`, default 2).
3. **Dependency Step**: Automatically runs dependency installations (e.g. `npm install`) inside ticket worktrees before testing.
4. **QA Verification**: Runs the configured test command (real process return code, not simulated).
5. **Reviewer**: Evaluates the diff against ticket criteria. If issues are found, feedback is sent back for rework (up to `STUDIO_MAX_REWORK_ROUNDS`).
6. **Merge Gate**: Fast-forwards or replays changes on the main project branch. Conflicts automatically trigger a rework attempt.
7. **Human Approval Gate** *(Optional)*: If enabled, requires human confirmation on diffs before merging.
8. **Auto-Resume**: If interrupted or killed, restarting the project retries blocked tickets with previous reviewer/QA feedback intact.

---

## Pixel Office Simulation

The Pixel Office visualizes real-time teamwork on an interactive 2D canvas:

* **Role Desks & Stations**:
  * **Manager**: Plans tickets at the desk and whiteboard (`★`).
  * **Developers**: Work in parallel at dedicated desk banks (`>`).
  * **QA Engineer**: Moves to the testing rig with live screen animations (`$`).
  * **Reviewer**: Inspects commits at the reviewer station (`@`).
* **Team Meetings**:
  * **Sprint Planning**: Team gathers at the conference table while the manager plans.
  * **Emergency Huddle**: Triggered automatically when a ticket gets blocked.
  * **Project Wrap-Up**: Post-completion debrief around the table.
* **Leisure & Open-Space Pastimes**:
  * Free agents awaiting tasks move to the open lounge area.
  * Randomized activities: **table tennis** (with animated ball rallies), **chess** matches, and informal **coffee chats** (quiet speech bubbles with zero token utilization).

---

## API Reference

### Software Studio Endpoints

| Method & Route | Description |
| :--- | :--- |
| `POST /studio/projects` | Create a project (`name`, `goal`, `repo_url`, `test_command`, `engine`, `developers`, etc.) and start the team. |
| `GET /studio/projects/{id}` | Get status, active team members, tickets, and current activities. |
| `GET /studio/projects/{id}/board` | Get tickets structured for Kanban display (TODO, IN_PROGRESS, TESTING, REVIEW, DONE, BLOCKED). |
| `GET /studio/projects/{id}/events?after=N` | Stream/poll recent project activity events. |
| `GET /studio/projects/{id}/diff` | View commit history and accumulated project diff. |
| `POST /studio/projects/{id}/start` | Start or resume an interrupted, blocked, or failed project. |
| `POST /studio/projects/{id}/cancel` | Gracefully cancel a running project. |
| `POST /studio/projects/{id}/messages` | Broadcast guidance or instructions to all team agent briefs. |
| `POST /studio/projects/{id}/ask` | Query the manager for status updates or architectural explanations. |
| `POST /studio/projects/{id}/tickets/{ticket}/approve` | Approve a pending ticket when `require_approval` is enabled. |
| `POST /studio/projects/{id}/tickets/{ticket}/reject` | Reject a pending ticket with revision instructions. |
| `DELETE /studio/projects/{id}` | Delete a project and optionally clean up workspace files. |
| `WS /office/ws?token=<token>` | Real-time WebSocket feed for office events and agent coordinates. |

---

## Authentication & Multi-Tenancy

Every database entity is scoped by `tenant_id`. Authentication is handled via JWT Bearer tokens or the platform administrator API key.

```bash
# 1. Create a tenant using the admin key
curl -X POST http://localhost:8000/tenants \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "slug": "acme"}'

# 2. Create the first user inside the tenant
curl -X POST http://localhost:8000/identity/users \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "<TENANT_ID>", "email": "dev@acme.com", "full_name": "Lead Dev", "password": "SecurePassword123"}'

# 3. Log in to get an access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@acme.com", "password": "SecurePassword123"}'

# 4. Access Studio API with Bearer token
curl http://localhost:8000/studio/projects \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

*(To bypass authentication during local development, set `AUTH_REQUIRED=false` in `.env`)*

---

## Safety Limits

* **Filesystem Boundary**: Agents are confined to their project scratch workspace (`STUDIO_WORKSPACES_DIR`). Directory traversal attempts outside the workspace boundary are rejected.
* **Command Allowlist**: Process executions run strictly without shell interpolation using an allowlist (`STUDIO_ALLOWED_COMMANDS`). Secrets and sensitive environment variables are stripped.
* **Network & Git Isolation**: Dangerous operations such as `git push`, `git pull`, `git remote`, and global package installations are blocked.

---

## Testing

```bash
# Run all test suites
pytest

# Run fast unit tests (~500 tests in under 2 minutes)
pytest tests/unit

# Run software studio multi-agent integration tests
pytest tests/integration/test_studio_teamwork.py

# Typecheck and build frontend
cd frontend && npm run build
```

---

## Repository Structure

```
agency/
├── src/
│   ├── domain/               # Core entities, state machines, events, value objects
│   ├── application/          # Agent loops, developer team orchestrator, studio service
│   ├── infrastructure/       # SQLAlchemy models, repositories, coding tools, command runner
│   └── api/                  # FastAPI routers, authentication, tenant context, schemas
├── frontend/
│   ├── src/studio/           # Software Studio dashboard & Kanban view
│   ├── src/studio/office/    # Pixel Office canvas engine, scene layout, leisure animations
│   └── src/components/       # UI controls, modals, and legacy dashboard views
├── migrations/               # Alembic database migrations (001–040)
├── scripts/                  # Standalone CLI tools and Phase 1-41 demonstration scripts
└── tests/
    ├── unit/                 # Domain and service unit tests
    ├── integration/          # Multi-agent teamwork and repository integration tests
    ├── security/             # Prompt injection, auth, and sandbox tests
    ├── concurrency/          # Multi-tenant and concurrent execution tests
    └── failure_injection/    # Fault recovery and circuit breaker tests
```
