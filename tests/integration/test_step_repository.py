"""
Integration tests for ExecutionStep repository persistence using async SQLAlchemy.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.agent import Agent
from src.domain.run import AgentRun
from src.domain.step import ExecutionStep, StepStatus, StepType
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
async def test_step_repository_save_and_list(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    agent = Agent(id="ag_step1", name="Step Agent", role="Worker")
    await agent_repo.save(agent)

    run = AgentRun(id="run_s1", agent_id="ag_step1", objective="Multi-step test")
    await run_repo.save(run)

    step1 = ExecutionStep(
        id="st_1",
        run_id="run_s1",
        step_number=1,
        step_type=StepType.INITIALIZE,
        input_data={"param": "value"},
    )
    step2 = ExecutionStep(
        id="st_2",
        run_id="run_s1",
        step_number=2,
        step_type=StepType.BUILD_CONTEXT,
    )

    await step_repo.save(step1)
    await step_repo.save(step2)

    # Update step 1 status
    step1.mark_completed(output_data={"initialized": True})
    await step_repo.save(step1)

    steps = await step_repo.list_by_run_id("run_s1")
    assert len(steps) == 2
    assert steps[0].id == "st_1"
    assert steps[0].status == StepStatus.COMPLETED
    assert steps[0].output_data == {"initialized": True}
    assert steps[1].id == "st_2"
    assert steps[1].status == StepStatus.STARTED
