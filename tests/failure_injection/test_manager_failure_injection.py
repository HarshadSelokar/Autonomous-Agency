"""
Failure-Injection Test Suite covering Phase 3 Manager & Organizational Orchestration failure modes.
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.employee_selector import EmployeeSelector
from src.application.employee_service import EmployeeService
from src.application.manager_orchestration_service import ManagerOrchestrationService
from src.application.plan_validator import PlanValidator
from src.domain.agent import Agent, ModelConfiguration
from src.domain.assignment import AssignmentStatus
from src.domain.decision import DecisionType
from src.domain.employee import Employee, EmployeeSkill, EmployeeStatus, SkillProficiency
from src.domain.exceptions import (
    AssignmentError,
    EmployeeValidationError,
    InvalidStateTransitionError,
    PlanValidationError,
)
from src.domain.objective import Objective, ObjectiveStatus
from src.domain.plan import Plan, PlanStatus
from src.domain.work_item import WorkItem, WorkItemStatus
from src.infrastructure.database import Base
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.assignment_repository import SQLAlchemyAssignmentRepository
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
from src.infrastructure.repositories.plan_repository import SQLAlchemyPlanRepository
from src.infrastructure.repositories.work_item_repository import SQLAlchemyWorkItemRepository


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def orchestration_setup(async_session: AsyncSession):
    obj_repo = SQLAlchemyObjectiveRepository(async_session)
    plan_repo = SQLAlchemyPlanRepository(async_session)
    wi_repo = SQLAlchemyWorkItemRepository(async_session)
    asgn_repo = SQLAlchemyAssignmentRepository(async_session)
    dec_repo = SQLAlchemyDecisionRepository(async_session)
    emp_repo = SQLAlchemyEmployeeRepository(async_session)
    agent_repo = SQLAlchemyAgentRepository(async_session)
    mock_engine = AsyncMock()

    plan_validator = PlanValidator()
    employee_selector = EmployeeSelector()
    employee_service = EmployeeService(emp_repo, agent_repo, mock_engine)

    service = ManagerOrchestrationService(
        objective_repo=obj_repo,
        plan_repo=plan_repo,
        work_item_repo=wi_repo,
        assignment_repo=asgn_repo,
        decision_repo=dec_repo,
        employee_repo=emp_repo,
        agent_repo=agent_repo,
        execution_engine=mock_engine,
        plan_validator=plan_validator,
        employee_selector=employee_selector,
    )

    return {
        "service": service,
        "emp_service": employee_service,
        "emp_repo": emp_repo,
        "agent_repo": agent_repo,
        "obj_repo": obj_repo,
        "plan_repo": plan_repo,
        "wi_repo": wi_repo,
        "asgn_repo": asgn_repo,
        "dec_repo": dec_repo,
        "session": async_session,
    }


async def create_test_agent_and_employee(
    agent_repo: SQLAlchemyAgentRepository,
    emp_repo: SQLAlchemyEmployeeRepository,
    emp_id: str,
    code: str,
    name: str,
    title: str,
    role: str,
    skills: list[EmployeeSkill] | None = None,
    status: EmployeeStatus = EmployeeStatus.ACTIVE,
    manager_id: str | None = None,
) -> Employee:
    ag_id = f"ag_{emp_id}"
    ag = Agent(
        id=ag_id,
        name=f"Agent {name}",
        role=role,
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
    )
    await agent_repo.save(ag)

    emp = Employee(
        id=emp_id,
        employee_code=code,
        name=name,
        title=title,
        role=role,
        agent_id=ag_id,
        skills=skills or [],
        status=status,
        manager_id=manager_id,
    )
    return await emp_repo.save(emp)


# 1. Direct Hierarchy Cycle Detection
@pytest.mark.asyncio
async def test_hierarchy_cycle_direct(orchestration_setup):
    emp_service: EmployeeService = orchestration_setup["emp_service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    await create_test_agent_and_employee(
        agent_repo, emp_repo, "m1", "M-1", "Manager 1", "Engineering Manager", "manager"
    )
    await create_test_agent_and_employee(
        agent_repo, emp_repo, "m2", "M-2", "Manager 2", "Engineering Manager", "manager"
    )

    await emp_service.update_manager(employee_id="m2", manager_id="m1")

    with pytest.raises(EmployeeValidationError, match="Circular manager hierarchy detected"):
        await emp_service.update_manager(employee_id="m1", manager_id="m2")


# 2. Transitive Hierarchy Cycle Detection
@pytest.mark.asyncio
async def test_hierarchy_cycle_transitive(orchestration_setup):
    emp_service: EmployeeService = orchestration_setup["emp_service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    await create_test_agent_and_employee(
        agent_repo, emp_repo, "m1", "M-1", "M1", "Director", "director"
    )
    await create_test_agent_and_employee(agent_repo, emp_repo, "m2", "M-2", "M2", "Lead", "manager")
    await create_test_agent_and_employee(agent_repo, emp_repo, "m3", "M-3", "M3", "Lead", "manager")

    await emp_service.update_manager(employee_id="m2", manager_id="m1")
    await emp_service.update_manager(employee_id="m3", manager_id="m2")

    with pytest.raises(EmployeeValidationError, match="Circular manager hierarchy detected"):
        await emp_service.update_manager(employee_id="m1", manager_id="m3")


# 3. Self-Management Rejection
@pytest.mark.asyncio
async def test_self_management_rejected(orchestration_setup):
    emp_service: EmployeeService = orchestration_setup["emp_service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    await create_test_agent_and_employee(agent_repo, emp_repo, "m1", "M-1", "M1", "Lead", "manager")

    with pytest.raises(EmployeeValidationError, match="cannot be assigned as their own manager"):
        await emp_service.update_manager(employee_id="m1", manager_id="m1")


# 4. Submit Plan with Non-Manager Employee
@pytest.mark.asyncio
async def test_submit_plan_non_manager(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    ic = await create_test_agent_and_employee(
        agent_repo, emp_repo, "dev1", "D-1", "Dev", "Software Engineer", "developer"
    )
    obj = await service.create_objective(
        objective_id="obj-1", title="Refactor", description="Refactor REST routes", requester="CEO"
    )

    wi = WorkItem(
        id="wi-1",
        plan_id="plan-1",
        title="Task",
        description="Desc",
        required_capabilities=["python"],
    )
    proposed_plan = Plan(id="plan-1", objective_id=obj.id, manager_id=ic.id, work_items=[wi])

    with pytest.raises(PlanValidationError, match="unauthorized"):
        await service.submit_and_validate_plan(proposed_plan)


# 5. Submit Plan with Inactive Manager
@pytest.mark.asyncio
async def test_submit_plan_inactive_manager(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    obj = await service.create_objective(
        objective_id="obj-1", title="Security Audit", description="Perform audit", requester="CTO"
    )

    mgr.transition_to(EmployeeStatus.INACTIVE)
    await emp_repo.save(mgr)

    wi = WorkItem(
        id="wi-1",
        plan_id="plan-1",
        title="Audit",
        description="Audit auth",
        required_capabilities=["security"],
    )
    proposed_plan = Plan(id="plan-1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    with pytest.raises(PlanValidationError, match="unauthorized"):
        await service.submit_and_validate_plan(proposed_plan)


# 6. Plan Validation - Empty Work Items
@pytest.mark.asyncio
async def test_plan_validation_empty_workitems(orchestration_setup):
    validator = PlanValidator()
    plan = Plan(
        id="p1",
        objective_id="obj-1",
        manager_id="mgr-1",
        work_items=[],
    )

    with pytest.raises(PlanValidationError, match="at least one work item"):
        validator.validate_proposed_plan(plan)


# 7. Plan Validation - Duplicate Work Item IDs
@pytest.mark.asyncio
async def test_plan_validation_duplicate_ids(orchestration_setup):
    validator = PlanValidator()
    wi1 = WorkItem(
        id="wi-1",
        plan_id="p1",
        title="Task 1",
        description="Desc 1",
        required_capabilities=["python"],
    )
    wi2 = WorkItem(
        id="wi-1", plan_id="p1", title="Task 2", description="Desc 2", required_capabilities=["sql"]
    )
    plan = Plan(
        id="p1",
        objective_id="obj-1",
        manager_id="mgr-1",
        work_items=[wi1, wi2],
    )

    with pytest.raises(PlanValidationError, match="Duplicate work item ID"):
        validator.validate_proposed_plan(plan)


# 8. Plan Validation - Missing Capability Specification
@pytest.mark.asyncio
async def test_plan_validation_missing_capability(orchestration_setup):
    validator = PlanValidator()
    wi1 = WorkItem(
        id="wi-1", plan_id="p1", title="Task 1", description="Desc 1", required_capabilities=[]
    )
    plan = Plan(
        id="p1",
        objective_id="obj-1",
        manager_id="mgr-1",
        work_items=[wi1],
    )

    with pytest.raises(PlanValidationError, match="must specify at least one required capability"):
        validator.validate_proposed_plan(plan)


# 9. Assign Work Item to Inactive Employee
@pytest.mark.asyncio
async def test_assign_workitem_inactive_employee(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    dev = await create_test_agent_and_employee(
        agent_repo,
        emp_repo,
        "dev1",
        "D-1",
        "Dev",
        "Developer",
        "developer",
        skills=[EmployeeSkill(name="python", proficiency=SkillProficiency.EXPERT)],
    )

    obj = await service.create_objective(
        objective_id="obj-1", title="Build Service", description="Service build", requester="CTO"
    )
    wi = WorkItem(
        id="wi-1",
        plan_id="p1",
        title="Endpoint 1",
        description="Create route",
        required_capabilities=["python"],
    )
    plan = Plan(id="p1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    await service.submit_and_validate_plan(plan)
    await service.approve_plan(plan.id, manager_id=mgr.id)

    # Deactivate developer
    dev.transition_to(EmployeeStatus.INACTIVE)
    await emp_repo.save(dev)

    with pytest.raises(AssignmentError, match="cannot be assigned work"):
        await service.assign_work_item(
            work_item_id="wi-1", employee_id=dev.id, assigned_by_manager_id=mgr.id
        )


# 10. Assign Work Item Missing Required Capability
@pytest.mark.asyncio
async def test_assign_workitem_missing_capability(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    designer = await create_test_agent_and_employee(
        agent_repo,
        emp_repo,
        "des1",
        "D-2",
        "UI Designer",
        "Designer",
        "designer",
        skills=[EmployeeSkill(name="figma", proficiency=SkillProficiency.EXPERT)],
    )

    obj = await service.create_objective(
        objective_id="obj-1", title="Backend Pipeline", description="DB Pipeline", requester="CTO"
    )
    wi = WorkItem(
        id="wi-backend",
        plan_id="p1",
        title="SQL Migration",
        description="Write migration",
        required_capabilities=["python", "fastapi"],
    )
    plan = Plan(id="p1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    await service.submit_and_validate_plan(plan)
    await service.approve_plan(plan.id, manager_id=mgr.id)

    with pytest.raises(AssignmentError, match="lacks required capabilities"):
        await service.assign_work_item(
            work_item_id="wi-backend", employee_id=designer.id, assigned_by_manager_id=mgr.id
        )


# 11. Invalid Objective State Transition - Submit Plan on Completed Objective
@pytest.mark.asyncio
async def test_invalid_objective_state_transition_submit_plan(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]
    obj_repo: SQLAlchemyObjectiveRepository = orchestration_setup["obj_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )

    obj = await service.create_objective(
        objective_id="obj-1", title="Quick Task", description="Fast task", requester="VP"
    )
    wi = WorkItem(
        id="wi-1", plan_id="p1", title="Task", description="Fast", required_capabilities=["python"]
    )
    plan = Plan(id="p1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    await service.submit_and_validate_plan(plan)
    await service.approve_plan(plan.id, manager_id=mgr.id)

    # Transition objective through REVIEWING to COMPLETED
    exec_obj = await service.get_objective(obj.id)
    exec_obj.transition_to(ObjectiveStatus.REVIEWING)
    exec_obj.transition_to(ObjectiveStatus.COMPLETED)
    await obj_repo.save(exec_obj)

    # Submit plan on completed objective
    wi2 = WorkItem(
        id="wi-2",
        plan_id="p2",
        title="Task 2",
        description="Another",
        required_capabilities=["python"],
    )
    late_plan = Plan(id="p2", objective_id=obj.id, manager_id=mgr.id, work_items=[wi2])

    with pytest.raises(InvalidStateTransitionError):
        await service.submit_and_validate_plan(late_plan)


# 12. Invalid Objective State Transition - Complete directly from RECEIVED
@pytest.mark.asyncio
async def test_invalid_objective_state_transition_complete(orchestration_setup):
    obj_repo: SQLAlchemyObjectiveRepository = orchestration_setup["obj_repo"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    obj = Objective(
        id="obj-direct",
        title="Direct Complete Test",
        description="Testing direct complete",
        requester="CTO",
        manager_id=mgr.id,
    )
    await obj_repo.save(obj)

    with pytest.raises(InvalidStateTransitionError):
        obj.transition_to(ObjectiveStatus.COMPLETED)


# 13. Invalid Objective State Transition - Clarify when EXECUTING
@pytest.mark.asyncio
async def test_invalid_objective_state_transition_clarification(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    obj = await service.create_objective(
        objective_id="obj-1", title="Clarify Test", description="Clarification test", requester="PM"
    )
    wi = WorkItem(
        id="wi-1",
        plan_id="p1",
        title="Task 1",
        description="Task 1 desc",
        required_capabilities=["python"],
    )
    plan = Plan(id="p1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    await service.submit_and_validate_plan(plan)
    await service.approve_plan(plan.id, manager_id=mgr.id)

    with pytest.raises(InvalidStateTransitionError):
        await service.provide_clarification(objective_id=obj.id, answers={"Q": "A"})


# 14. EmployeeSelector - No Capability Match
@pytest.mark.asyncio
async def test_employee_selector_no_match(orchestration_setup):
    selector = EmployeeSelector()
    dev = Employee(
        id="dev1",
        employee_code="D-1",
        name="Dev",
        title="Developer",
        role="developer",
        agent_id="ag1",
        skills=[EmployeeSkill(name="python", proficiency=SkillProficiency.INTERMEDIATE)],
        status=EmployeeStatus.ACTIVE,
    )

    eligible = selector.find_eligible_employees(
        employees=[dev], required_capabilities=["k8s", "terraform"]
    )
    assert len(eligible) == 0


# 15. EmployeeSelector - Eligible Active Candidates
@pytest.mark.asyncio
async def test_employee_selector_workload_balancing(orchestration_setup):
    selector = EmployeeSelector()
    e1 = Employee(
        id="dev1",
        employee_code="D-1",
        name="Dev 1",
        title="Developer",
        role="developer",
        agent_id="ag1",
        skills=[EmployeeSkill(name="python", proficiency=SkillProficiency.EXPERT)],
        status=EmployeeStatus.ACTIVE,
    )
    e2 = Employee(
        id="dev2",
        employee_code="D-2",
        name="Dev 2",
        title="Developer",
        role="developer",
        agent_id="ag2",
        skills=[EmployeeSkill(name="python", proficiency=SkillProficiency.EXPERT)],
        status=EmployeeStatus.INACTIVE,
    )

    eligible = selector.find_eligible_employees(
        employees=[e1, e2], required_capabilities=["python"]
    )
    assert len(eligible) == 1
    assert eligible[0].id == e1.id


# 16. Blocker Escalation and Reassignment Resolution Flow
@pytest.mark.asyncio
async def test_blocker_escalation_and_resolution(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    dev1 = await create_test_agent_and_employee(
        agent_repo,
        emp_repo,
        "dev1",
        "D-1",
        "Dev 1",
        "Developer",
        "developer",
        skills=[EmployeeSkill(name="python", proficiency=SkillProficiency.EXPERT)],
    )
    dev2 = await create_test_agent_and_employee(
        agent_repo,
        emp_repo,
        "dev2",
        "D-2",
        "Dev 2",
        "Developer",
        "developer",
        skills=[EmployeeSkill(name="python", proficiency=SkillProficiency.EXPERT)],
    )

    obj = await service.create_objective(
        objective_id="obj-1", title="Blocked Flow", description="Testing blocker", requester="VP"
    )
    wi = WorkItem(
        id="wi-blocked",
        plan_id="p1",
        title="Task",
        description="Desc",
        required_capabilities=["python"],
    )
    plan = Plan(id="p1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    await service.submit_and_validate_plan(plan)
    await service.approve_plan(plan.id, manager_id=mgr.id)
    await service.assign_work_item(
        work_item_id=wi.id, employee_id=dev1.id, assigned_by_manager_id=mgr.id
    )

    # Handle blocker
    wi_blocked = await service.handle_blocker(
        work_item_id=wi.id,
        objective_id=obj.id,
        employee_id=dev1.id,
        reason="Missing API key credentials",
    )
    assert wi_blocked.status == WorkItemStatus.BLOCKED

    # Manager reassigns to dev2
    asgn_resumed = await service.reassign_work_item(
        work_item_id=wi.id,
        new_employee_id=dev2.id,
        assigned_by_manager_id=mgr.id,
        reason="Reassigned with key",
    )
    assert asgn_resumed.employee_id == dev2.id
    assert asgn_resumed.status == AssignmentStatus.ACTIVE


# 17. Reassign Non-Existent Work Item Failure
@pytest.mark.asyncio
async def test_reassign_non_existent_workitem(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    dev = await create_test_agent_and_employee(
        agent_repo,
        emp_repo,
        "dev1",
        "D-1",
        "Dev",
        "Developer",
        "developer",
        skills=[EmployeeSkill(name="python", proficiency=SkillProficiency.EXPERT)],
    )

    with pytest.raises(AssignmentError, match="WorkItem 'non-existent-id' not found"):
        await service.reassign_work_item(
            work_item_id="non-existent-id",
            new_employee_id=dev.id,
            assigned_by_manager_id=mgr.id,
            reason="Missing",
        )


# 18. Decision Audit Trail Integrity
@pytest.mark.asyncio
async def test_decision_audit_trail_recorded(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    top_mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr_top", "M-TOP", "Director", "Director", "director"
    )
    sub_mgr = await create_test_agent_and_employee(
        agent_repo,
        emp_repo,
        "mgr_sub",
        "M-SUB",
        "Lead",
        "Lead Manager",
        "manager",
        manager_id=top_mgr.id,
    )

    dec = await service.escalate_work_item(
        work_item_id="wi_1", objective_id="obj_1", manager_id=sub_mgr.id, reason="Resource conflict"
    )

    assert dec.decision_type == DecisionType.ESCALATE
    assert dec.manager_id == sub_mgr.id
    assert "mgr_top" in dec.selected_action


# 19. Plan Rejection State Machine Flow
@pytest.mark.asyncio
async def test_plan_rejection_flow(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    obj = await service.create_objective(
        objective_id="obj-1",
        title="Reject Plan Objective",
        description="Testing rejection",
        requester="CTO",
    )

    wi = WorkItem(
        id="wi-1", plan_id="p1", title="Task", description="Desc", required_capabilities=["python"]
    )
    plan = Plan(id="p1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    await service.submit_and_validate_plan(plan)

    # Reject plan directly via plan object transition
    plan.status = PlanStatus.REJECTED
    await orchestration_setup["plan_repo"].save(plan)

    obj.transition_to(ObjectiveStatus.CLARIFICATION_REQUIRED)
    await orchestration_setup["obj_repo"].save(obj)

    updated_obj = await service.get_objective(obj.id)
    assert updated_obj.status == ObjectiveStatus.CLARIFICATION_REQUIRED


# 20. Objective Cancellation State Enforcement
@pytest.mark.asyncio
async def test_objective_cancellation_state(orchestration_setup):
    service: ManagerOrchestrationService = orchestration_setup["service"]
    emp_repo: SQLAlchemyEmployeeRepository = orchestration_setup["emp_repo"]
    agent_repo: SQLAlchemyAgentRepository = orchestration_setup["agent_repo"]

    mgr = await create_test_agent_and_employee(
        agent_repo, emp_repo, "mgr1", "M-1", "Manager", "Engineering Manager", "manager"
    )
    obj = await service.create_objective(
        objective_id="obj-cancel",
        title="Obsolete Objective",
        description="To cancel",
        requester="CTO",
    )

    obj.transition_to(ObjectiveStatus.CANCELLED)
    await orchestration_setup["obj_repo"].save(obj)

    wi = WorkItem(
        id="wi-1", plan_id="p1", title="Task", description="Desc", required_capabilities=["python"]
    )
    plan = Plan(id="p1", objective_id=obj.id, manager_id=mgr.id, work_items=[wi])

    with pytest.raises(InvalidStateTransitionError):
        await service.submit_and_validate_plan(plan)
