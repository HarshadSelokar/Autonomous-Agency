# Autonomous AI Organization Platform — Agent Runtime Foundation (Phase 1)

This repository implements the **Agent Runtime Foundation** for the Autonomous AI Organization Platform.

## Core Architectural Boundary

```
Company OS  →  Employee / Agent  →  Agent Runtime  →  Model Provider Interface  →  GroqModelProvider
```

- **The LLM is NOT the Agent**: An LLM is only a provider used by the runtime.
- **Authoritative State**: Owned by the Agent Runtime & Company OS, never directly by the LLM.
- **Provider Independence**: Pure domain & application layers decoupled from Groq or any specific LLM provider.

## Directory Structure

- `src/domain/`: Pure business models, state machines, value objects, exceptions, interfaces.
- `src/application/`: Execution engine, context builder, retry logic, structured output validator.
- `src/infrastructure/`: Groq SDK integration, PostgreSQL (SQLAlchemy), Alembic migrations, logging.
- `src/api/`: FastAPI application, endpoints, Pydantic request/response models.
- `tests/`: Unit, integration, and failure injection tests.

## Local Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```
