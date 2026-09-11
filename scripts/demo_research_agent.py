"""
Phase 1 Demonstration Script — Research Agent Execution.
Demonstrates the foundational Agent Runtime pipeline:
Agent -> AgentRun -> Context -> ModelProvider -> Response Normalization -> Persistence -> Audit.
"""

import asyncio
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.agent_loader import load_agent_from_yaml
from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import default_provider_registry
from src.infrastructure.config import settings
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.providers.groq_provider import GroqModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.checkpoint_repository import SQLAlchemyCheckpointRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository


async def run_demo() -> None:
    print("=" * 80)
    print("AUTONOMOUS AI COMPANY PLATFORM - PHASE 1 DEMONSTRATION")
    print("=" * 80)

    # 1. Initialize Engine & Session Factory (using async engine)
    db_url = os.environ.get("DEMO_DATABASE_URL", "sqlite+aiosqlite:///agent_runtime_demo.db")
    demo_engine = create_async_engine(db_url, echo=False)
    async_session_factory = async_sessionmaker(demo_engine, expire_on_commit=False)

    async with demo_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Register Model Providers
    groq_api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        print("[SETUP] Groq API key detected. Using live GroqModelProvider.")
        default_provider_registry.register(GroqModelProvider(api_key=groq_api_key))
    else:
        print("[SETUP] GROQ_API_KEY not configured. Using deterministic FakeModelProvider.")
        default_provider_registry.register(
            FakeModelProvider(
                canned_content=(
                    "PostgreSQL offers ACID compliance, extensible JSONB data types, "
                    "pgvector support for embeddings, and robust transaction isolation. "
                    "Limitations for AI platforms include high concurrency write scaling "
                    "which requires read-replicas or sharding."
                )
            )
        )

    # 3. Load Agent from YAML configuration
    agent_config_path = "config/agents/researcher.yaml"
    agent = load_agent_from_yaml(agent_config_path)

    # Fallback provider configuration if Groq key is missing
    if not groq_api_key:
        agent.model_configuration = agent.model_configuration.__class__(
            provider="fake", model="fake-model"
        )

    print(f"[AGENT LOADED] ID: {agent.id} | Name: {agent.name} | Role: {agent.role}")
    print(
        f"               Provider: {agent.model_configuration.provider} | "
        f"Model: {agent.model_configuration.model}"
    )

    # 4. Save Agent to Persistence Repository
    async with async_session_factory() as session:
        agent_repo = SQLAlchemyAgentRepository(session)
        run_repo = SQLAlchemyAgentRunRepository(session)
        step_repo = SQLAlchemyExecutionStepRepository(session)
        chk_repo = SQLAlchemyCheckpointRepository(session)

        await agent_repo.save(agent)
        await session.commit()

        # 5. Initialize Execution Engine
        engine_inst = AgentExecutionEngine(
            agent_repo=agent_repo,
            run_repo=run_repo,
            step_repo=step_repo,
            checkpoint_repo=chk_repo,
        )

        objective = "Explain the benefits and limitations of PostgreSQL for an AI company platform."
        print(f"\n[EXECUTION STARTING] Objective: '{objective}'")

        # 6. Execute Run
        run = await engine_inst.execute_run(
            agent_id=agent.id,
            objective=objective,
        )
        await session.commit()

        # 7. Audit & Results Output
        print("\n" + "=" * 80)
        print("EXECUTION AUDIT SUMMARY")
        print("=" * 80)
        print(f"Run ID:          {run.id}")
        print(f"Agent ID:        {run.agent_id}")
        print(f"Status:          {run.status.value}")
        print(f"Provider/Model:  {run.provider} / {run.model}")
        print(f"Started At:      {run.started_at}")
        print(f"Completed At:    {run.completed_at}")
        print(f"Token Usage:     {json.dumps(run.usage)}")

        print("\n[EXECUTION STEPS]")
        steps = await step_repo.list_by_run_id(run.id)
        for step in steps:
            print(
                f"  Step {step.step_number}: [{step.step_type.value.upper()}] "
                f"Status: {step.status.value}"
            )

        print("\n[CHECKPOINTS RECORDED]")
        chks = await chk_repo.list_by_run_id(run.id)
        for chk in chks:
            print(
                f"  Checkpoint ID: {chk.id} | Step: {chk.current_step} | "
                f"State: {chk.current_state}"
            )

        print("\n[PRODUCED MODEL RESULT]")
        if run.result:
            print(f"{run.result.get('content')}")
        print("=" * 80)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY.")

    await demo_engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_demo())
