"""
Integration tests for Swarm Execution Topologies & Coordination Modes (Phase 22).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.swarm_coordination_engine import SwarmCoordinationEngine
from src.application.swarm_service import SwarmService
from src.domain.swarm import CoordinationMode, SwarmStatus
from src.infrastructure.models.company_model import Base
from src.infrastructure.repositories.swarm_repository import SQLAlchemySwarmRepository


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_pipeline_coordination_mode_execution(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    service = SwarmService(swarm_repo=repo)
    coord_engine = SwarmCoordinationEngine()

    swarm = await service.create_swarm(
        parent_task_id="task-pipe-100",
        name="Pipeline Swarm",
        purpose="Execute sequential pipeline",
        manager_id="emp-mgr-1",
        coordination_mode=CoordinationMode.PIPELINE,
    )

    formed = await service.plan_and_form_swarm(
        swarm_id=swarm.id,
        task_title="Pipeline Processing",
        task_description="Sequential stage 1 to stage 3",
        required_capabilities=["research", "code_generation", "testing"],
    )

    # In PIPELINE mode, only stage 1 is executable first
    executable = coord_engine.determine_executable_members(formed, set())
    assert len(executable) == 1
    assert executable[0].id == formed.members[0].id

    # Once stage 1 completes, stage 2 becomes executable
    executable_stage2 = coord_engine.determine_executable_members(formed, {formed.members[0].id})
    assert len(executable_stage2) == 1
    assert executable_stage2[0].id == formed.members[1].id


@pytest.mark.asyncio
async def test_map_reduce_coordination_mode_execution(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    service = SwarmService(swarm_repo=repo)
    coord_engine = SwarmCoordinationEngine()

    swarm = await service.create_swarm(
        parent_task_id="task-mr-100",
        name="Map-Reduce Swarm",
        purpose="Parallel map processing and reduce synthesis",
        manager_id="emp-mgr-1",
        coordination_mode=CoordinationMode.MAP_REDUCE,
    )

    formed = await service.plan_and_form_swarm(
        swarm_id=swarm.id,
        task_title="Batch Synthesis",
        task_description="Map workers synthesis",
        required_capabilities=["research", "testing"],
    )

    # In MAP_REDUCE mode, all non-reduce members execute first
    executable_map = coord_engine.determine_executable_members(formed, set())
    assert len(executable_map) >= 1
