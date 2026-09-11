"""
Unit & Integration tests for AgentRun Cancellation.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.execution_engine import AgentExecutionEngine
from src.domain.agent import Agent, AgentState
from src.domain.run import AgentRun, RunStatus
from src.infrastructure.database import Base
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
async def test_cancel_run_updates_run_and_agent_states(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    agent = Agent(id="ag_cancel", name="Cancel Test Agent", role="Worker")
    agent.transition_to(AgentState.READY)
    agent.transition_to(AgentState.RUNNING)
    await agent_repo.save(agent)

    run = AgentRun(id="run_to_cancel", agent_id="ag_cancel", objective="Task to be cancelled")
    run.transition_to(RunStatus.INITIALIZING)
    run.transition_to(RunStatus.RUNNING)
    await run_repo.save(run)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
    )

    cancelled_run = await engine.cancel_run("run_to_cancel", reason="User stopped run")

    assert cancelled_run.status == RunStatus.CANCELLED
    assert cancelled_run.failure_reason == "User stopped run"
    assert cancelled_run.completed_at is not None

    # Verify agent state reset to READY
    updated_agent = await agent_repo.get_by_id("ag_cancel")
    assert updated_agent is not None
    assert updated_agent.current_state == AgentState.READY
