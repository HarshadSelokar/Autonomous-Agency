# Autonomous AI Organization Platform

A FastAPI backend that models a company whose employees are AI agents, plus a React
"Pixel Office" dashboard. The part that does real work today is the **Software Studio**:
give a small team of agents a goal and a git repository, and they plan it, write the code,
run the tests, review the diff and commit.

## Status

Under development, not production ready.

| Area | State |
| :--- | :--- |
| Software Studio (manager, developer, QA, reviewer on a real repo) | Working end to end |
| Agent runtime, tasks, governance, model routing, memory, tools (phases 1-13) | Implemented and tested |
| Authentication (bearer tokens, admin API key) | Enforced on every route except `/health` and `/auth/login` |
| Tenant isolation | Enforced for every table in the database layer: the tenant comes from the credential, and reads, updates and deletes are scoped to it |
| Business, GTM, venture, enterprise modules (phases 14-31) | Data models and deterministic services; no model-driven behaviour |
| Phases 32-41 (workflow v2, audit, resilience, control plane) | Stored in the database; exposed through `/control-plane` |
| Databases | Migrations `001`-`040` and the main flows verified on PostgreSQL 18 and SQLite |
| Pixel Office frontend | Dashboard with mock-data fallback; not yet driven by the studio |

## Quick start

```bash
pip install -e ".[dev]"
cp .env.example .env          # then fill in the values below
alembic upgrade head
uvicorn src.api.main:app --reload --port 8000
```

Set these in `.env`:

- `GROQ_API_KEY` (or `OPENAI_API_KEY` with `STUDIO_PROVIDER=openai`). Check `GROQ_MODEL`
  names a model your key can use; Groq retires models over time.
- `AUTH_SECRET_KEY`: signing key for access tokens.
- `ADMIN_API_KEY`: sent as `X-API-Key`, acts as platform administrator.
- `AUTH_REQUIRED=false` switches authentication off for local experiments.

## Software Studio

### From the command line (no database needed)

```bash
python -m scripts.run_studio_project "Add a /version endpoint with a test" \
    --repo path/to/your/repo --test "python -m pytest -q"
```

The repository is cloned into `scratch/studio/<project-id>`; the original is never
modified. Commits land on the branch `agency/<project-id>` in that clone. Nothing is pushed.

### Through the API

| Endpoint | Purpose |
| :--- | :--- |
| `POST /studio/projects` | Create a project (`name`, `goal`, optional `repo_url`, `test_command`, `engine`, `model`, `developers`, `require_approval`) and start the team |
| `GET /studio/projects/{id}` | Status, team members with their current activity, tickets |
| `GET /studio/projects/{id}/board` | Tickets grouped into kanban columns |
| `GET /studio/projects/{id}/events?after=N` | Activity feed ("reading app.py", "running tests", ...) |
| `GET /studio/projects/{id}/diff` | Commits and diff the team has produced |
| `POST /studio/projects/{id}/start` | Restart an interrupted, failed or cancelled project |
| `POST /studio/projects/{id}/cancel` | Stop at the team's next step |
| `POST /studio/projects/{id}/team`, `PATCH`/`DELETE .../team/{member}` | Add, rename or remove agents while the project is not running |
| `POST /studio/projects/{id}/messages` | Give the team an instruction; every later brief carries it |
| `POST /studio/projects/{id}/ask` | Ask the manager about the project (read-only) |
| `POST /studio/projects/{id}/tickets/{ticket}/approve` or `/reject` | Your sign-off on a ticket when `require_approval` is on |

Activity is also pushed to `/office/ws` WebSocket clients as it happens.

### Engines

A project runs on one of two engines, chosen with `STUDIO_ENGINE`, the `--engine` flag, or
the `engine` field of `POST /studio/projects`:

| Engine | What does the work | Needs |
| :--- | :--- | :--- |
| `loop` | Our own agent loop and coding tools against Groq or an OpenAI-compatible API | An API key |
| `agy` | The Antigravity CLI, run headless once per role | `agy` installed and signed in; no API key |

```bash
python -m scripts.run_studio_project "Add a /version endpoint with a test"     --repo path/to/your/repo --test "python -m pytest -q" --engine agy
```

With `agy`, each role uses its own model (`AGY_MODEL_MANAGER`, `AGY_MODEL_DEVELOPER`,
`AGY_MODEL_REVIEWER`), and a model that runs out of quota is retried once on
`AGY_FALLBACK_MODEL`. The agent edits files but is not given permission to run commands:
tests are run by the QA step under our command allowlist, and failures go back to the
developer. `agy` enforces its own file boundaries, not ours: a write outside the project
cannot be prevented, but it is detected, the attempt is discarded and the ticket is redone.

### How a project runs

1. **Manager** gets a snapshot of the repository and breaks the goal into tickets.
2. **Developers** work tickets at the same time (`STUDIO_DEVELOPERS`, default 2), each in its
   own git worktree, so they never edit the same directory. A ticket waits for the tickets
   it depends on.
3. **QA** runs the project's test command. This is a real process exit code, not a model's opinion.
4. **Reviewer** reads the diff and approves or sends it back.
5. With `require_approval`, the ticket then waits for you to approve or reject it.
6. Approved work is merged into the project branch, one ticket at a time. If other tickets
   were merged meanwhile, the change is replayed on top of them and the tests run again; a
   conflict sends the ticket back to its developer.
7. A ticket that fails any step goes back with the reason, up to `STUDIO_MAX_REWORK_ROUNDS`
   times, then is marked `BLOCKED` and its unmerged work is discarded.

The team is also registered in the employee and agent tables. If the API restarts, running
projects resume by themselves (finished tickets are kept). If every model is out of quota,
the project waits `STUDIO_QUOTA_RETRY_MINUTES` and resumes.

### Safety limits

- Agents can only touch files inside the project workspace.
- Commands run without a shell, one program per call, from an allowlist
  (`STUDIO_ALLOWED_COMMANDS`), with secrets removed from the environment and a timeout.
- `git push`, `pull`, `fetch`, `clone` and `remote` are refused; so are global package installs,
  and Python package installs outside a workspace virtualenv.
- This is a policy boundary, not an OS sandbox. An allowed program (for example `python`) can
  still reach the network and the rest of the disk. Run the API in a container or VM before
  pointing it at code you do not trust.

## Authentication

```bash
# Create a tenant and its first user with the admin key
curl -X POST localhost:8000/tenants -H "X-API-Key: $ADMIN_API_KEY" \
     -H "Content-Type: application/json" -d '{"name": "Acme", "slug": "acme"}'
curl -X POST localhost:8000/identity/users -H "X-API-Key: $ADMIN_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"tenant_id": "<id>", "email": "you@example.com", "full_name": "You", "password": "<10+ chars>"}'

# Log in and call the API
curl -X POST localhost:8000/auth/login -H "Content-Type: application/json" \
     -d '{"email": "you@example.com", "password": "<password>"}'
curl localhost:8000/studio/projects -H "Authorization: Bearer <access_token>"
```

WebSocket clients pass the token as `/office/ws?token=<access_token>`.

## Project structure

- `src/domain/`: entities, state machines, events, exceptions.
- `src/application/`: services. `agent_loop.py` (multi-step tool loop), `dev_team_service.py`
  (the team), `studio_service.py` (background runs), plus the company-model services.
- `src/infrastructure/`: SQLAlchemy models and repositories, model providers (Groq,
  OpenAI-compatible), `coding/` (workspace, command runner, coding tools), `security/`.
- `src/api/`: FastAPI routes, schemas, middleware.
- `migrations/`: Alembic migrations `001`-`040`.
- `frontend/`: React + Vite Pixel Office dashboard.
- `tests/`: unit, integration, security, failure-injection and concurrency suites.

## Tests

```bash
pytest
```

`tests/conftest.py` clears provider keys, points the suite at an in-memory database and turns
authentication off, so tests never call a real model or touch your real database. Authentication tests switch it back on themselves.
