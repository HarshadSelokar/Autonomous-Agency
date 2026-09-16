"""
Unit and integration tests for Swarm Application Services & Coordination Engine (Phase 22).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.swarm_coordination_engine import SwarmCoordinationEngine
from src.application.swarm_planner import SwarmPlanner
from src.application.swarm_service import SwarmService
from src.domain.exceptions import SwarmBudgetExceededError, SwarmDepthExceededError
from src.domain.swarm import CoordinationMode, SwarmMemberStatus, SwarmMessageType, SwarmStatus
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


def test_swarm_planner_topology_generation():
    planner = SwarmPlanner(max_allowed_depth=2)
    plan = planner.plan_swarm(
        parent_task_id="task-100",
        task_title="Investigate software bug in payment engine",
        task_description="Perform root cause analysis and implement fix",
        required_capabilities=["research", "code_generation", "testing", "security_review"],
        requested_mode=CoordinationMode.SPECIALIST,
    )

    assert plan.coordination_mode == CoordinationMode.SPECIALIST
    assert len(plan.member_requirements) == 6
    assert plan.member_requirements[0].capability == "research"
    assert plan.member_requirements[2].capability == "code_generation"


def test_swarm_planner_depth_exceeded_raises():
    planner = SwarmPlanner(max_allowed_depth=2)
    with pytest.raises(SwarmDepthExceededError):
        planner.plan_swarm(
            parent_task_id="task-101",
            task_title="Nested Swarm",
            task_description="Deep swarm",
            required_capabilities=["code_generation"],
            depth=3,  # Exceeds max depth 2
        )


def test_coordination_engine_pipeline_flow():
    engine = SwarmCoordinationEngine()
    # Test pipeline sequential execution eligibility...
    assert engine is not None


@pytest.mark.asyncio
async def test_swarm_service_full_lifecycle(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    service = SwarmService(swarm_repo=repo)

    # 1. Create Swarm
    swarm = await service.create_swarm(
        parent_task_id="task-200",
        name="Full Lifecycle Swarm",
        purpose="Investigate and implement feature X",
        manager_id="emp-mgr-1",
        coordination_mode=CoordinationMode.SPECIALIST,
    )
    assert swarm.status == SwarmStatus.CREATED

    # 2. Plan and Form
    formed_swarm = await service.plan_and_form_swarm(
        swarm_id=swarm.id,
        task_title="Investigate and implement feature X",
        task_description="Complete feature development lifecycle",
        required_capabilities=["research", "architecture", "code_generation", "testing"],
    )
    assert formed_swarm.status == SwarmStatus.READY
    assert len(formed_swarm.members) == 6

    # 3. Start Swarm
    running_swarm = await service.start_swarm(swarm.id)
    assert running_swarm.status == SwarmStatus.RUNNING

    # 4. Execute Subtasks for members
    m1 = running_swarm.members[0]
    output1 = await service.execute_member_subtask(
        swarm_id=swarm.id,
        member_id=m1.id,
        objective="Requirements Analysis",
        duration_seconds=30,
        model_cost=1.2,
        tool_calls=4,
        tokens=2000,
    )
    assert output1["status"] == "COMPLETED"

    # 5. Send inter-agent message
    m2 = running_swarm.members[1]
    msg = await service.send_inter_agent_message(
        swarm_id=swarm.id,
        sender_id=m1.agent_id,
        recipient_id=m2.agent_id,
        message_type=SwarmMessageType.HANDOFF,
        payload={"requirements_summary": "Passed requirements specs"},
    )
    assert msg.message_type == SwarmMessageType.HANDOFF

    # 6. Complete Swarm
    member_results = {
        m1.id: output1,
        m2.id: {"status": "COMPLETED", "output": "Architecture complete"},
    }
    result = await service.complete_swarm(swarm.id, member_results)
    assert result.is_completed
    assert result.verification_status == "VERIFIED"


@pytest.mark.asyncio
async def test_swarm_budget_exhaustion_pauses_swarm(async_session: AsyncSession):
    repo = SQLAlchemySwarmRepository(async_session)
    service = SwarmService(swarm_repo=repo)

    swarm = await service.create_swarm(
        parent_task_id="task-300",
        name="Low Budget Swarm",
        purpose="Test budget enforcement",
        manager_id="emp-mgr-1",
        custom_budget={"max_execution_time_seconds": 10},
    )
    formed = await service.plan_and_form_swarm(
        swarm_id=swarm.id,
        task_title="Quick Task",
        task_description="Low budget test",
        required_capabilities=["code_generation"],
    )
    await service.start_swarm(swarm.id)

    m1 = formed.members[0]


    with pytest.raises(SwarmBudgetExceededError):
        await service.execute_member_subtask(
            swarm_id=swarm.id,
            member_id=m1.id,
            objective="Exceed time budget",
            duration_seconds=20,  # Exceeds budget 10s
        )

    updated = await repo.get_by_id(swarm.id)
    assert updated.status == SwarmStatus.PAUSED
