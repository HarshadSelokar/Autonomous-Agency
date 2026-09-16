"""
Integration tests for Swarm Failure Injection & Recovery (Phase 22).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.swarm_service import SwarmService
from src.domain.exceptions import SwarmBudgetExceededError
from src.domain.swarm import CoordinationMode, SwarmMemberStatus, SwarmStatus
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
async def test_member_failure_and_recovery_reassignment(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    service = SwarmService(swarm_repo=repo)

    swarm = await service.create_swarm(
        parent_task_id="task-fail-100",
        name="Failure Recovery Swarm",
        purpose="Test failure recovery",
        manager_id="emp-mgr-1",
    )

    formed = await service.plan_and_form_swarm(
        swarm_id=swarm.id,
        task_title="Resilience Test",
        task_description="Worker process failure test",
        required_capabilities=["code_generation"],
    )

    await service.start_swarm(swarm.id)
    m1 = formed.members[0]

    # Handle member failure
    recovered = await service.handle_member_failure(
        swarm_id=swarm.id,
        member_id=m1.id,
        reason="Worker process killed by OS kernel OOM killer",
    )

    assert recovered.status == SwarmMemberStatus.ACTIVE
    assert recovered.execution_stats["error_reason"] == "Worker process killed by OS kernel OOM killer"


@pytest.mark.asyncio
async def test_swarm_pause_and_resume_governance_controls(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    service = SwarmService(swarm_repo=repo)

    swarm = await service.create_swarm(
        parent_task_id="task-pause-100",
        name="Governed Pause Swarm",
        purpose="Test lifecycle pause and resume",
        manager_id="emp-mgr-1",
    )
    await service.plan_and_form_swarm(
        swarm_id=swarm.id,
        task_title="Pause Task",
        task_description="Pause test",
        required_capabilities=["code_generation"],
    )
    await service.start_swarm(swarm.id)

    paused = await service.pause_swarm(swarm.id)
    assert paused.status == SwarmStatus.PAUSED

    resumed = await service.resume_swarm(swarm.id)
    assert resumed.status == SwarmStatus.RUNNING

