"""
Unit tests for SQLAlchemy Swarm Repository (Phase 22).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.swarm import (
    CoordinationMode,
    Swarm,
    SwarmBudget,
    SwarmConflict,
    SwarmMember,
    SwarmMemberStatus,
    SwarmMessage,
    SwarmMessageType,
    SwarmResult,
    SwarmStatus,
)
from src.infrastructure.models.company_model import Base
from src.infrastructure.models.swarm_model import SwarmModel
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
async def test_swarm_repository_crud(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)

    swarm = Swarm(
        id="swarm-100",
        name="Security Review Swarm",
        code="SW-SEC-100",
        parent_task_id="task-500",
        purpose="Run static analysis and penetration test suite",
        manager_id="emp-mgr-1",
        coordination_mode=CoordinationMode.SPECIALIST,
    )

    mem1 = SwarmMember(
        id="sm-1",
        swarm_id=swarm.id,
        employee_id="emp-1",
        agent_id="agent-1",
        role="Security Auditor",
        capability="security_review",
        status=SwarmMemberStatus.ACTIVE,
    )
    swarm.add_member(mem1)

    saved_swarm = await repo.save(swarm)
    assert saved_swarm.id == "swarm-100"

    fetched = await repo.get_by_id("swarm-100")
    assert fetched is not None
    assert fetched.name == "Security Review Swarm"
    assert fetched.coordination_mode == CoordinationMode.SPECIALIST
    assert len(fetched.members) == 1
    assert fetched.members[0].role == "Security Auditor"


@pytest.mark.asyncio
async def test_swarm_budget_repository(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    swarm = Swarm(
        id="swarm-200",
        name="Budget Test Swarm",
        code="SW-BDG-200",
        parent_task_id="task-501",
        purpose="Test budget persistence",
        manager_id="emp-mgr-1",
    )
    await repo.save(swarm)

    budget = SwarmBudget(
        swarm_id=swarm.id,
        max_execution_time_seconds=1800,
        max_model_cost=25.0,
        max_tool_calls=100,
        max_tokens=250000,
    )
    await repo.save_budget(budget)

    fetched_budget = await repo.get_budget(swarm.id)
    assert fetched_budget is not None
    assert fetched_budget.max_model_cost == 25.0
    assert fetched_budget.max_tool_calls == 100


@pytest.mark.asyncio
async def test_swarm_message_and_conflict_repository(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    swarm = Swarm(
        id="swarm-300",
        name="Message Test Swarm",
        code="SW-MSG-300",
        parent_task_id="task-502",
        purpose="Test inter-agent messaging",
        manager_id="emp-mgr-1",
    )
    await repo.save(swarm)

    msg = SwarmMessage(
        id="msg-1",
        swarm_id=swarm.id,
        sender_id="agent-1",
        recipient_id="agent-2",
        task_id="task-502",
        message_type=SwarmMessageType.HANDOFF,
        payload={"output_ref": "art-123"},
    )
    await repo.save_message(msg)

    messages = await repo.list_messages_by_swarm(swarm.id)
    assert len(messages) == 1
    assert messages[0].message_type == SwarmMessageType.HANDOFF
    assert messages[0].payload["output_ref"] == "art-123"
