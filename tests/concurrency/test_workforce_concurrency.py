"""Concurrency test suite for Phase 15 Dynamic Workforce Engine."""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.team import Team, TeamStatus, TeamType
from src.infrastructure.database import Base
from src.infrastructure.repositories.team_repository import SQLAlchemyTeamRepository
from src.infrastructure.repositories.workforce_repository import SQLAlchemyWorkforceRepository


@pytest.fixture
async def db_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    yield session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_simultaneous_team_creation_concurrency(db_session_factory):
    """
    CONCURRENCY TEST:
    Simultaneous team creation attempts with distinct team codes succeed concurrently without race conditions.
    """
    async def _create_team(code: str, name: str):
        async with db_session_factory() as session:
            repo = SQLAlchemyTeamRepository(session)
            team = Team(name=name, code=code, purpose="Concurrent test", team_type=TeamType.PROJECT)
            team.activate()
            await repo.save(team)

    tasks = [_create_team(f"TC-{i}", f"Team-{i}") for i in range(5)]
    await asyncio.gather(*tasks)

    async with db_session_factory() as session:
        repo = SQLAlchemyTeamRepository(session)
        teams = await repo.list_all()
        assert len(teams) == 5
