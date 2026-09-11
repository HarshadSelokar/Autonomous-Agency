"""
Integration tests for AgentCheckpoint repository persistence using async SQLAlchemy.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.agent import Agent
from src.domain.checkpoint import AgentCheckpoint
from src.domain.run import AgentRun
from src.infrastructure.database import Base
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.checkpoint_repository import SQLAlchemyCheckpointRepository
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
async def test_checkpoint_repository_save_and_get_latest(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    chk_repo = SQLAlchemyCheckpointRepository(async_session)

    agent = Agent(id="ag_chk", name="Checkpoint Agent", role="Worker")
    await agent_repo.save(agent)

    run = AgentRun(id="run_chk1", agent_id="ag_chk", objective="Checkpoint test")
    await run_repo.save(run)

    chk1 = AgentCheckpoint(
        id="chk_1",
        run_id="run_chk1",
        current_state="RUNNING",
        current_step=1,
        output_so_far={"part": 1},
    )
    chk2 = AgentCheckpoint(
        id="chk_2",
        run_id="run_chk1",
        current_state="RUNNING",
        current_step=2,
        output_so_far={"part": 2},
    )

    await chk_repo.save(chk1)
    await chk_repo.save(chk2)

    latest = await chk_repo.get_latest_by_run_id("run_chk1")
    assert latest is not None
    assert latest.id == "chk_2"
    assert latest.current_step == 2
    assert latest.output_so_far == {"part": 2}

    all_chks = await chk_repo.list_by_run_id("run_chk1")
    assert len(all_chks) == 2
    assert [c.id for c in all_chks] == ["chk_1", "chk_2"]
