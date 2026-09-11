"""
Integration tests for AgentExecutionEngine execution pipeline.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import ModelProviderRegistry
from src.domain.agent import Agent, AgentState, ModelConfiguration
from src.domain.exceptions import ProviderUnavailableError
from src.domain.run import RunStatus
from src.domain.step import StepStatus, StepType
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository


@pytest.fixture
async def async_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_execution_engine_successful_run(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    # Register fake model provider
    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider(
        canned_content="PostgreSQL offers ACID compliance and strong durability."
    )
    registry.register(fake_provider)

    # Save agent with provider "fake"
    agent = Agent(
        id="researcher_test",
        name="Researcher",
        role="researcher",
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
    )
    await agent_repo.save(agent)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
    )

    # Execute run
    run = await engine.execute_run(
        agent_id="researcher_test",
        objective="Explain PostgreSQL benefits",
    )

    assert run.status == RunStatus.COMPLETED
    assert run.result is not None
    assert run.result["content"] == "PostgreSQL offers ACID compliance and strong durability."
    assert run.usage["total_tokens"] == 30

    # Verify agent state reset to READY
    updated_agent = await agent_repo.get_by_id("researcher_test")
    assert updated_agent is not None
    assert updated_agent.current_state == AgentState.READY

    # Verify execution steps
    steps = await step_repo.list_by_run_id(run.id)
    assert len(steps) == 5
    assert [s.step_type for s in steps] == [
        StepType.INITIALIZE,
        StepType.BUILD_CONTEXT,
        StepType.MODEL_CALL,
        StepType.VALIDATE_RESPONSE,
        StepType.FINALIZE,
    ]
    assert all(s.status == StepStatus.COMPLETED for s in steps)


@pytest.mark.asyncio
async def test_execution_engine_provider_failure_updates_run_state(
    async_session: AsyncSession,
) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider(
        should_fail_with=ProviderUnavailableError("Fake service unavailable")
    )
    registry.register(fake_provider)

    agent = Agent(
        id="agent_fail_test",
        name="Fail Agent",
        role="Worker",
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
    )
    await agent_repo.save(agent)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
    )

    with pytest.raises(ProviderUnavailableError):
        await engine.execute_run(
            agent_id="agent_fail_test",
            objective="Will fail",
        )

    # Check run state marked FAILED
    runs = await run_repo.list_by_agent_id("agent_fail_test")
    assert len(runs) == 1
    failed_run = runs[0]
    assert failed_run.status == RunStatus.FAILED
    assert "Fake service unavailable" in (failed_run.failure_reason or "")
