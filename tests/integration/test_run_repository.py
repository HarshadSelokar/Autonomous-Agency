"""
Integration tests for AgentRun repository persistence using async SQLAlchemy.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.agent import Agent
from src.domain.run import AgentRun, RunStatus
from src.infrastructure.database import Base
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository


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
async def test_agent_run_repository_save_and_get(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)

    # Agent foreign key requirement
    agent = Agent(id="agent_r1", name="Runner Agent", role="Worker")
    await agent_repo.save(agent)

    run = AgentRun(
        id="run_101",
        agent_id="agent_r1",
        objective="Execute task 101",
        provider="groq",
        model="llama-3.3-70b-versatile",
    )

    # Save
    await run_repo.save(run)

    # Get by ID
    fetched = await run_repo.get_by_id("run_101")
    assert fetched is not None
    assert fetched.id == "run_101"
    assert fetched.agent_id == "agent_r1"
    assert fetched.status == RunStatus.CREATED


@pytest.mark.asyncio
async def test_agent_run_repository_status_update(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)

    agent = Agent(id="agent_r2", name="Runner Agent 2", role="Worker")
    await agent_repo.save(agent)

    run = AgentRun(id="run_102", agent_id="agent_r2", objective="Execute task 102")
    await run_repo.save(run)

    # Transition
    run.transition_to(RunStatus.INITIALIZING)
    run.transition_to(RunStatus.RUNNING)
    run.usage = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
    run.result = {"answer": "Task output"}
    run.transition_to(RunStatus.COMPLETED)
    await run_repo.save(run)

    updated = await run_repo.get_by_id("run_102")
    assert updated is not None
    assert updated.status == RunStatus.COMPLETED
    assert updated.usage["total_tokens"] == 150
    assert updated.result == {"answer": "Task output"}


@pytest.mark.asyncio
async def test_agent_run_repository_list_by_agent_id(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)

    agent = Agent(id="agent_r3", name="Runner Agent 3", role="Worker")
    await agent_repo.save(agent)

    r1 = AgentRun(id="run_201", agent_id="agent_r3", objective="Objective 1")
    r2 = AgentRun(id="run_202", agent_id="agent_r3", objective="Objective 2")
    await run_repo.save(r1)
    await run_repo.save(r2)

    runs = await run_repo.list_by_agent_id("agent_r3")
    assert len(runs) == 2
    assert {r.id for r in runs} == {"run_201", "run_202"}
