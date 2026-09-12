"""
Integration tests for Phase 3 Repositories using SQLite in-memory database.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.agent import Agent, ModelConfiguration
from src.domain.assignment import Assignment
from src.domain.decision import DecisionType, ManagerDecision
from src.domain.employee import Employee
from src.domain.objective import Objective
from src.domain.plan import Plan
from src.domain.work_item import WorkItem
from src.infrastructure.database import Base
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.assignment_repository import SQLAlchemyAssignmentRepository
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
from src.infrastructure.repositories.plan_repository import SQLAlchemyPlanRepository
from src.infrastructure.repositories.work_item_repository import SQLAlchemyWorkItemRepository


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
async def test_phase3_repositories_crud(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    emp_repo = SQLAlchemyEmployeeRepository(async_session)
    obj_repo = SQLAlchemyObjectiveRepository(async_session)
    plan_repo = SQLAlchemyPlanRepository(async_session)
    wi_repo = SQLAlchemyWorkItemRepository(async_session)
    asgn_repo = SQLAlchemyAssignmentRepository(async_session)
    dec_repo = SQLAlchemyDecisionRepository(async_session)

    # Setup Agent & Employee (Manager)
    agent = Agent(
        id="ag_mgr_01",
        name="Manager Agent",
        role="Manager",
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
    )
    await agent_repo.save(agent)

    mgr = Employee(
        id="emp_bob_mgr",
        employee_code="EMP-BOB",
        name="Bob Manager",
        title="Engineering Manager",
        role="manager",
        agent_id="ag_mgr_01",
    )
    await emp_repo.save(mgr)

    # 1. Objective Repository
    objective = Objective(
        id="obj_analytics_01",
        title="Build CSV Analytics App",
        description="Develop CSV parsing and dashboard visualization application.",
        requester="CTO",
        manager_id="emp_bob_mgr",
    )
    saved_obj = await obj_repo.save(objective)
    assert saved_obj.id == "obj_analytics_01"

    found_obj = await obj_repo.get_by_id("obj_analytics_01")
    assert found_obj is not None
    assert found_obj.title == "Build CSV Analytics App"

    # 2. Plan & WorkItem Repositories
    wi1 = WorkItem(
        id="wi_arch_01",
        plan_id="plan_analytics_01",
        title="Define System Architecture",
        description="Design backend REST endpoints",
        required_capabilities=["architecture"],
    )
    plan = Plan(
        id="plan_analytics_01",
        objective_id="obj_analytics_01",
        manager_id="emp_bob_mgr",
        goals=["Build web backend"],
        work_items=[wi1],
    )

    saved_plan = await plan_repo.save(plan)
    assert saved_plan.id == "plan_analytics_01"
    assert len(saved_plan.work_items) == 1

    found_plan = await plan_repo.get_by_objective_id("obj_analytics_01")
    assert found_plan is not None
    assert len(found_plan.work_items) == 1
    assert found_plan.work_items[0].title == "Define System Architecture"

    # 3. WorkItem standalone Repository lookup
    found_wi = await wi_repo.get_by_id("wi_arch_01")
    assert found_wi is not None
    assert found_wi.plan_id == "plan_analytics_01"

    # 4. Assignment Repository
    assignment = Assignment(
        id="asgn_01",
        work_item_id="wi_arch_01",
        employee_id="emp_bob_mgr",
        assigned_by="emp_bob_mgr",
        reason="Initial assignment for architecture design",
    )
    saved_asgn = await asgn_repo.save(assignment)
    assert saved_asgn.id == "asgn_01"

    asgns = await asgn_repo.list_by_work_item_id("wi_arch_01")
    assert len(asgns) == 1

    # 5. Manager Decision Repository
    decision = ManagerDecision(
        id="dec_01",
        manager_id="emp_bob_mgr",
        objective_id="obj_analytics_01",
        decision_type=DecisionType.APPROVE_PLAN,
        reasoning_summary="Plan is sound and complete",
        selected_action="Approve plan and assign architecture work item",
    )
    saved_dec = await dec_repo.save(decision)
    assert saved_dec.id == "dec_01"

    decs = await dec_repo.list_by_objective_id("obj_analytics_01")
    assert len(decs) == 1
