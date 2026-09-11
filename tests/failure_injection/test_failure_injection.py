"""
Failure-Injection Test Suite covering all 12 Phase 1 resilient failure modes.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import ModelProviderRegistry
from src.application.retry import RetryPolicy
from src.application.structured_output import StructuredOutputValidator
from src.domain.agent import Agent, AgentState, ModelConfiguration
from src.domain.checkpoint import AgentCheckpoint
from src.domain.exceptions import (
    ConfigurationError,
    InvalidResponseError,
    InvalidStateTransitionError,
    ProviderUnavailableError,
    RateLimitError,
    StructuredOutputValidationError,
    TimeoutError,
)
from src.domain.run import AgentRun, RunStatus
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.checkpoint_repository import SQLAlchemyCheckpointRepository
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


# 1. Model Timeout
@pytest.mark.asyncio
async def test_failure_injection_model_timeout(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider(should_fail_with=TimeoutError("Model call timed out"))
    registry.register(fake_provider)

    agent = Agent(id="ag_timeout", name="Timeout Agent", role="Worker")
    agent.model_configuration = ModelConfiguration(provider="fake", model="fake-model")
    await agent_repo.save(agent)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
        retry_policy=RetryPolicy(max_retries=1, backoff_factor=0.01),
    )

    with pytest.raises(TimeoutError):
        await engine.execute_run("ag_timeout", "Objective timeout")

    runs = await run_repo.list_by_agent_id("ag_timeout")
    assert runs[0].status == RunStatus.FAILED
    assert "timed out" in (runs[0].failure_reason or "")


# 2. Provider Unavailable
@pytest.mark.asyncio
async def test_failure_injection_provider_unavailable(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider(
        should_fail_with=ProviderUnavailableError("503 Service Unavailable")
    )
    registry.register(fake_provider)

    agent = Agent(id="ag_unavail", name="Unavail Agent", role="Worker")
    agent.model_configuration = ModelConfiguration(provider="fake", model="fake-model")
    await agent_repo.save(agent)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
        retry_policy=RetryPolicy(max_retries=1, backoff_factor=0.01),
    )

    with pytest.raises(ProviderUnavailableError):
        await engine.execute_run("ag_unavail", "Objective unavail")

    runs = await run_repo.list_by_agent_id("ag_unavail")
    assert runs[0].status == RunStatus.FAILED


# 3. Rate Limit
@pytest.mark.asyncio
async def test_failure_injection_rate_limit(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider(should_fail_with=RateLimitError("429 Rate limit exceeded"))
    registry.register(fake_provider)

    agent = Agent(id="ag_ratelimit", name="Ratelimit Agent", role="Worker")
    agent.model_configuration = ModelConfiguration(provider="fake", model="fake-model")
    await agent_repo.save(agent)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
        retry_policy=RetryPolicy(max_retries=1, backoff_factor=0.01),
    )

    with pytest.raises(RateLimitError):
        await engine.execute_run("ag_ratelimit", "Objective ratelimit")


# 4. Invalid Model Response
@pytest.mark.asyncio
async def test_failure_injection_invalid_response(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider(should_fail_with=InvalidResponseError("Malformed response"))
    registry.register(fake_provider)

    agent = Agent(id="ag_invalid_resp", name="Invalid Resp Agent", role="Worker")
    agent.model_configuration = ModelConfiguration(provider="fake", model="fake-model")
    await agent_repo.save(agent)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
    )

    with pytest.raises(InvalidResponseError):
        await engine.execute_run("ag_invalid_resp", "Objective invalid response")


# 5. Invalid Structured Output
def test_failure_injection_invalid_structured_output() -> None:
    validator = StructuredOutputValidator()
    schema = {"required": ["summary", "findings"]}

    with pytest.raises(StructuredOutputValidationError):
        validator.validate(content='{"summary": "Only summary"}', expected_schema=schema)


# 6. Database Failure
@pytest.mark.asyncio
async def test_failure_injection_database_failure(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider()
    registry.register(fake_provider)

    # Save agent
    agent = Agent(id="ag_db_fail", name="DB Fail Agent", role="Worker")
    agent.model_configuration = ModelConfiguration(provider="fake", model="fake-model")
    await agent_repo.save(agent)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
    )

    # Close DB session prematurely to simulate DB network partition
    await async_session.close()

    with pytest.raises(Exception):  # noqa: B017
        await engine.execute_run("ag_db_fail", "Objective DB fail")


# 7. Cancellation
@pytest.mark.asyncio
async def test_failure_injection_cancellation(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    agent = Agent(id="ag_cancel_inj", name="Cancel Inj Agent", role="Worker")
    await agent_repo.save(agent)

    run = AgentRun(id="run_inj_cancel", agent_id="ag_cancel_inj", objective="Obj")
    run.transition_to(RunStatus.INITIALIZING)
    run.transition_to(RunStatus.RUNNING)
    await run_repo.save(run)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
    )

    cancelled = await engine.cancel_run("run_inj_cancel", reason="Explicit cancellation")
    assert cancelled.status == RunStatus.CANCELLED


# 8. Retry Exhaustion
@pytest.mark.asyncio
async def test_failure_injection_retry_exhaustion() -> None:
    policy = RetryPolicy(max_retries=2, backoff_factor=0.01)
    call_count = 0

    async def fail_always():
        nonlocal call_count
        call_count += 1
        raise TimeoutError("Always timeout")

    with pytest.raises(TimeoutError):
        await policy.execute(fail_always)

    assert call_count == 3  # 1 initial + 2 retries


# 9. Invalid Agent State Transition
def test_failure_injection_invalid_agent_state_transition() -> None:
    agent = Agent(id="ag_inv_st", name="Inv State Agent", role="Worker")
    with pytest.raises(InvalidStateTransitionError):
        agent.transition_to(AgentState.COMPLETED)  # Cannot go IDLE -> COMPLETED directly


# 10. Invalid Run State Transition
def test_failure_injection_invalid_run_state_transition() -> None:
    run = AgentRun(id="run_inv_st", agent_id="ag", objective="Obj")
    with pytest.raises(InvalidStateTransitionError):
        run.transition_to(RunStatus.COMPLETED)  # Cannot go CREATED -> COMPLETED directly


# 11. Checkpoint Failure & Restoration
@pytest.mark.asyncio
async def test_failure_injection_checkpoint_restore(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    chk_repo = SQLAlchemyCheckpointRepository(async_session)

    agent = Agent(id="ag_chk_restore", name="Chk Agent", role="Worker")
    await agent_repo.save(agent)

    run = AgentRun(id="run_chk_restore", agent_id="ag_chk_restore", objective="Obj")
    await run_repo.save(run)

    chk = AgentCheckpoint(
        id="chk_restore_1",
        run_id="run_chk_restore",
        current_state="RUNNING",
        current_step=3,
        output_so_far={"progress": "50%"},
    )
    await chk_repo.save(chk)

    # Restore from repository
    restored = await chk_repo.get_latest_by_run_id("run_chk_restore")
    assert restored is not None
    assert restored.current_step == 3
    assert restored.output_so_far == {"progress": "50%"}


# 12. Missing Provider Configuration
def test_failure_injection_missing_provider_configuration() -> None:
    registry = ModelProviderRegistry()
    with pytest.raises(ConfigurationError):
        registry.get("non_existent_provider")
