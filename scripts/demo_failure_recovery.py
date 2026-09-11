"""
Phase 1 Failure & Recovery Demonstration Script.
Demonstrates:
1. Provider Failure & Bounded Retry Exhaustion (Run = FAILED)
2. Safe Run Cancellation
3. Checkpoint Persistence & State Restoration
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import ModelProviderRegistry
from src.application.retry import RetryPolicy
from src.domain.agent import Agent, AgentState
from src.domain.checkpoint import AgentCheckpoint
from src.domain.exceptions import ProviderUnavailableError
from src.domain.run import AgentRun, RunStatus
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.checkpoint_repository import SQLAlchemyCheckpointRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository


async def run_failure_demos() -> None:
    print("=" * 80)
    print("PHASE 1 - RESILIENCE & FAILURE RECOVERY DEMONSTRATION")
    print("=" * 80)

    db_url = os.environ.get("DEMO_DATABASE_URL", "sqlite+aiosqlite:///agent_runtime_demo.db")
    demo_engine = create_async_engine(db_url, echo=False)
    async_session_factory = async_sessionmaker(demo_engine, expire_on_commit=False)

    async with demo_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # -------------------------------------------------------------
    # DEMO 1: Provider Failure & Bounded Retry Exhaustion
    # -------------------------------------------------------------
    print("\n--- DEMO 1: Provider Failure & Retry Exhaustion ---")
    failing_registry = ModelProviderRegistry()
    failing_provider = FakeModelProvider(
        should_fail_with=ProviderUnavailableError("Groq Service 503 Unavailable")
    )
    failing_registry.register(failing_provider)

    async with async_session_factory() as session:
        agent_repo = SQLAlchemyAgentRepository(session)
        run_repo = SQLAlchemyAgentRunRepository(session)
        step_repo = SQLAlchemyExecutionStepRepository(session)

        agent = Agent(id="ag_fail_demo", name="Resilience Test Agent", role="Tester")
        agent.model_configuration = agent.model_configuration.__class__(
            provider="fake", model="fake-model"
        )
        await agent_repo.save(agent)

        engine_inst = AgentExecutionEngine(
            agent_repo=agent_repo,
            run_repo=run_repo,
            step_repo=step_repo,
            provider_registry=failing_registry,
            retry_policy=RetryPolicy(max_retries=2, backoff_factor=0.01),
        )

        try:
            await engine_inst.execute_run(
                agent_id="ag_fail_demo",
                objective="Test bounded retries",
            )
        except ProviderUnavailableError as e:
            print(f"[EXPECTED EXCEPTION CAUGHT] {e}")

        await session.commit()

        runs = await run_repo.list_by_agent_id("ag_fail_demo")
        failed_run = runs[0]
        print(f"Persisted Run Status:  {failed_run.status.value}")
        print(f"Failure Reason:        {failed_run.failure_reason}")
        print(f"Provider Call Retries: {failing_provider.call_count} attempts made")

    # -------------------------------------------------------------
    # DEMO 2: Safe Cancellation
    # -------------------------------------------------------------
    print("\n--- DEMO 2: Safe AgentRun Cancellation ---")
    async with async_session_factory() as session:
        agent_repo = SQLAlchemyAgentRepository(session)
        run_repo = SQLAlchemyAgentRunRepository(session)
        step_repo = SQLAlchemyExecutionStepRepository(session)

        agent = Agent(id="ag_cancel_demo", name="Cancellation Agent", role="Worker")
        agent.transition_to(AgentState.READY)
        agent.transition_to(AgentState.RUNNING)
        await agent_repo.save(agent)

        run = AgentRun(
            id="run_to_cancel_demo",
            agent_id="ag_cancel_demo",
            objective="Long running simulation",
        )
        run.transition_to(RunStatus.INITIALIZING)
        run.transition_to(RunStatus.RUNNING)
        await run_repo.save(run)
        await session.commit()

        engine_inst = AgentExecutionEngine(
            agent_repo=agent_repo,
            run_repo=run_repo,
            step_repo=step_repo,
        )

        cancelled_run = await engine_inst.cancel_run(
            "run_to_cancel_demo", reason="Operator interrupted run"
        )
        await session.commit()

        print(f"Cancelled Run ID:      {cancelled_run.id}")
        print(f"New Status:            {cancelled_run.status.value}")
        print(f"Cancellation Reason:   {cancelled_run.failure_reason}")

        updated_agent = await agent_repo.get_by_id("ag_cancel_demo")
        if updated_agent:
            print(f"Agent State Reset To:  {updated_agent.current_state.value}")

    # -------------------------------------------------------------
    # DEMO 3: Execution Checkpointing & State Restoration
    # -------------------------------------------------------------
    print("\n--- DEMO 3: Checkpointing & State Restoration ---")
    async with async_session_factory() as session:
        agent_repo = SQLAlchemyAgentRepository(session)
        run_repo = SQLAlchemyAgentRunRepository(session)
        chk_repo = SQLAlchemyCheckpointRepository(session)

        agent = Agent(id="ag_chk_demo", name="Checkpoint Agent", role="Worker")
        await agent_repo.save(agent)

        run = AgentRun(id="run_chk_demo", agent_id="ag_chk_demo", objective="Checkpoint demo")
        await run_repo.save(run)

        # Save Checkpoint 1
        chk1 = AgentCheckpoint(
            id="chk_demo_1",
            run_id="run_chk_demo",
            current_state="RUNNING",
            current_step=1,
            output_so_far={"partial": "Step 1 complete"},
        )
        await chk_repo.save(chk1)

        # Save Checkpoint 2
        chk2 = AgentCheckpoint(
            id="chk_demo_2",
            run_id="run_chk_demo",
            current_state="RUNNING",
            current_step=2,
            output_so_far={"partial": "Step 1 & 2 complete"},
        )
        await chk_repo.save(chk2)
        await session.commit()

        print("[SIMULATED INTERRUPTION] Execution halted after step 2.")
        print("[RESTORATION] Fetching latest checkpoint from persistence...")

        restored_chk = await chk_repo.get_latest_by_run_id("run_chk_demo")
        if restored_chk:
            print(f"Restored Checkpoint ID: {restored_chk.id}")
            print(f"Restored Step Number:   {restored_chk.current_step}")
            print(f"Restored State:         {restored_chk.current_state}")
            print(f"Restored Output So Far: {restored_chk.output_so_far}")

    print("\n" + "=" * 80)
    print("RESILIENCE DEMONSTRATION COMPLETED SUCCESSFULLY.")

    await demo_engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_failure_demos())
