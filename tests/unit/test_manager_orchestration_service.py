"""
Unit tests for ManagerOrchestrationService.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.manager_orchestration_service import ManagerOrchestrationService
from src.domain.decision import DecisionType
from src.domain.employee import (
    Employee,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)
from src.domain.exceptions import (
    AssignmentError,
    ObjectiveValidationError,
)
from src.domain.objective import Objective, ObjectiveStatus
from src.domain.plan import Plan, PlanStatus
from src.domain.run import AgentRun, RunStatus
from src.domain.work_item import WorkItem

ReposTuple = tuple[
    AsyncMock, AsyncMock, AsyncMock, AsyncMock, AsyncMock, AsyncMock, AsyncMock, AsyncMock
]


@pytest.fixture
def mock_repos() -> ReposTuple:
    obj_repo = AsyncMock()
    plan_repo = AsyncMock()
    wi_repo = AsyncMock()
    asgn_repo = AsyncMock()
    dec_repo = AsyncMock()
    emp_repo = AsyncMock()
    agent_repo = AsyncMock()
    engine = AsyncMock()
    return obj_repo, plan_repo, wi_repo, asgn_repo, dec_repo, emp_repo, agent_repo, engine


@pytest.fixture
def manager_service(mock_repos: tuple) -> ManagerOrchestrationService:
    (
        obj_repo,
        plan_repo,
        wi_repo,
        asgn_repo,
        dec_repo,
        emp_repo,
        agent_repo,
        engine,
    ) = mock_repos

    obj_repo.get_by_id.return_value = None
    obj_repo.save.side_effect = lambda obj: obj
    plan_repo.get_by_id.return_value = None
    plan_repo.save.side_effect = lambda p: p
    wi_repo.get_by_id.return_value = None
    wi_repo.save.side_effect = lambda wi: wi
    asgn_repo.save.side_effect = lambda a: a
    dec_repo.save.side_effect = lambda d: d

    engine.execute_run.return_value = AgentRun(
        id="run_mgr_01",
        agent_id="ag_mgr_01",
        objective="Orchestrate objective",
        status=RunStatus.COMPLETED,
    )

    return ManagerOrchestrationService(
        objective_repo=obj_repo,
        plan_repo=plan_repo,
        work_item_repo=wi_repo,
        assignment_repo=asgn_repo,
        decision_repo=dec_repo,
        employee_repo=emp_repo,
        agent_repo=agent_repo,
        execution_engine=engine,
    )


@pytest.mark.asyncio
async def test_create_objective_success(manager_service: ManagerOrchestrationService) -> None:
    obj = await manager_service.create_objective(
        objective_id="obj_100",
        title="Analytics App",
        description="Build analytics tool",
        requester="CTO",
    )
    assert obj.id == "obj_100"
    assert obj.status == ObjectiveStatus.RECEIVED


@pytest.mark.asyncio
async def test_create_objective_non_manager_fails(
    manager_service: ManagerOrchestrationService, mock_repos: tuple
) -> None:
    _, _, _, _, _, emp_repo, _, _ = mock_repos
    non_mgr = Employee(
        id="emp_dev",
        employee_code="E-DEV",
        name="Dev",
        title="Developer",
        role="developer",
        agent_id="ag1",
        status=EmployeeStatus.ACTIVE,
    )
    emp_repo.get_by_id.return_value = non_mgr

    with pytest.raises(ObjectiveValidationError) as exc:
        await manager_service.create_objective(
            objective_id="obj_101",
            title="Title",
            description="Desc",
            requester="CTO",
            manager_id="emp_dev",
        )
    assert "does not possess managerial authority" in str(exc.value)


@pytest.mark.asyncio
async def test_clarification_flow(
    manager_service: ManagerOrchestrationService, mock_repos: tuple
) -> None:
    obj_repo = mock_repos[0]
    obj = Objective(
        id="obj_clarify",
        title="Ambiguous App",
        description="Build something cool",
        requester="Product",
        status=ObjectiveStatus.RECEIVED,
    )
    obj_repo.get_by_id.return_value = obj

    req_obj = await manager_service.request_clarification(
        "obj_clarify", questions=["Target users?", "Tech stack?"]
    )
    assert req_obj.status == ObjectiveStatus.CLARIFICATION_REQUIRED

    ans_obj = await manager_service.provide_clarification(
        "obj_clarify", answers={"Target users?": "Engineers", "Tech stack?": "Python"}
    )
    assert ans_obj.status == ObjectiveStatus.READY_FOR_PLANNING


@pytest.mark.asyncio
async def test_submit_and_approve_plan(
    manager_service: ManagerOrchestrationService, mock_repos: tuple
) -> None:
    obj_repo, plan_repo, wi_repo, asgn_repo, dec_repo, emp_repo, agent_repo, engine = mock_repos

    obj = Objective(
        id="obj_plan",
        title="Plan Objective",
        description="Description",
        requester="CEO",
        status=ObjectiveStatus.READY_FOR_PLANNING,
    )
    mgr = Employee(
        id="emp_mgr",
        employee_code="E-MGR",
        name="Bob Manager",
        title="Engineering Manager",
        role="manager",
        agent_id="ag_mgr",
        status=EmployeeStatus.ACTIVE,
    )
    obj_repo.get_by_id.return_value = obj
    emp_repo.get_by_id.return_value = mgr

    wi = WorkItem(
        id="wi_1",
        plan_id="p1",
        title="Build API",
        description="FastAPI",
        required_capabilities=["python"],
    )
    proposed_plan = Plan(
        id="p1", objective_id="obj_plan", manager_id="emp_mgr", work_items=[wi]
    )

    saved_plan, saved_obj = await manager_service.submit_and_validate_plan(proposed_plan)
    assert saved_plan.status == PlanStatus.PROPOSED
    assert saved_obj.status == ObjectiveStatus.PLANNED

    plan_repo.get_by_id.return_value = saved_plan
    approved_plan = await manager_service.approve_plan("p1", "emp_mgr")
    assert approved_plan.status == PlanStatus.APPROVED
    assert obj.status == ObjectiveStatus.EXECUTING


@pytest.mark.asyncio
async def test_assign_work_item_capability_validation(
    manager_service: ManagerOrchestrationService, mock_repos: tuple
) -> None:
    obj_repo, plan_repo, wi_repo, asgn_repo, dec_repo, emp_repo, agent_repo, engine = mock_repos

    wi = WorkItem(
        id="wi_py",
        plan_id="p1",
        title="Python Task",
        description="Python backend",
        required_capabilities=["python", "fastapi"],
    )
    wi_repo.get_by_id.return_value = wi

    mgr = Employee(
        id="mgr1",
        employee_code="E-MGR",
        name="Manager",
        title="Manager",
        role="manager",
        agent_id="ag_m",
        status=EmployeeStatus.ACTIVE,
    )
    emp_lacks_cap = Employee(
        id="emp_no_py",
        employee_code="E-NOPY",
        name="Java Dev",
        title="Developer",
        role="developer",
        agent_id="ag_j",
        skills=[EmployeeSkill(name="java", proficiency=SkillProficiency.EXPERT)],
        status=EmployeeStatus.ACTIVE,
    )

    def emp_get_by_id(emp_id: str) -> Employee | None:
        if emp_id == "mgr1":
            return mgr
        if emp_id == "emp_no_py":
            return emp_lacks_cap
        return None

    emp_repo.get_by_id.side_effect = emp_get_by_id

    with pytest.raises(AssignmentError) as exc:
        await manager_service.assign_work_item("wi_py", "emp_no_py", "mgr1")

    assert "lacks required capabilities" in str(exc.value)


@pytest.mark.asyncio
async def test_escalate_work_item(
    manager_service: ManagerOrchestrationService, mock_repos: tuple
) -> None:
    emp_repo = mock_repos[5]

    mgr = Employee(
        id="mgr_sub",
        employee_code="E-SUB",
        name="Lead",
        title="Lead",
        role="lead",
        agent_id="ag1",
        manager_id="mgr_top",
        status=EmployeeStatus.ACTIVE,
    )
    top_mgr = Employee(
        id="mgr_top",
        employee_code="E-TOP",
        name="Director",
        title="Director",
        role="director",
        agent_id="ag2",
        status=EmployeeStatus.ACTIVE,
    )

    def emp_get_by_id(emp_id: str) -> Employee | None:
        if emp_id == "mgr_sub":
            return mgr
        if emp_id == "mgr_top":
            return top_mgr
        return None

    emp_repo.get_by_id.side_effect = emp_get_by_id

    dec = await manager_service.escalate_work_item(
        work_item_id="wi_1",
        objective_id="obj_1",
        manager_id="mgr_sub",
        reason="Resource constraint",
    )

    assert dec.decision_type == DecisionType.ESCALATE
    assert "mgr_top" in dec.selected_action
