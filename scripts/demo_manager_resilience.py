"""
Phase 3 Demonstration Script — Manager Guardrails & Resilience.

Demonstrates runtime error handling and organizational guardrails:
1. Circular Manager Hierarchy Cycle Rejection (EmployeeValidationError)
2. Non-Manager Plan Proposal Rejection (PlanValidationError)
3. Capability Mismatch Assignment Protection (AssignmentError)
4. Invalid Objective State Machine Transition Protection (InvalidStateTransitionError)
"""

import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.employee_selector import EmployeeSelector
from src.application.employee_service import EmployeeService
from src.application.execution_engine import AgentExecutionEngine
from src.application.manager_orchestration_service import ManagerOrchestrationService
from src.application.plan_validator import PlanValidator
from src.application.provider_registry import default_provider_registry
from src.domain.agent import Agent, ModelConfiguration
from src.domain.employee import (
    Employee,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)
from src.domain.exceptions import (
    AssignmentError,
    EmployeeValidationError,
    InvalidStateTransitionError,
    PlanValidationError,
)
from src.domain.objective import ObjectiveStatus
from src.domain.plan import Plan
from src.domain.work_item import WorkItem
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.assignment_repository import SQLAlchemyAssignmentRepository
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
from src.infrastructure.repositories.plan_repository import SQLAlchemyPlanRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository
from src.infrastructure.repositories.work_item_repository import SQLAlchemyWorkItemRepository


async def run_resilience_demo() -> None:
    print("=" * 80)
    print("AUTONOMOUS AI COMPANY PLATFORM - PHASE 3 RESILIENCE & GUARDRAILS DEMO")
    print("=" * 80)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    default_provider_registry.register(FakeModelProvider(canned_content="Guardrail Output"))

    async with session_factory() as session:
        obj_repo = SQLAlchemyObjectiveRepository(session)
        plan_repo = SQLAlchemyPlanRepository(session)
        wi_repo = SQLAlchemyWorkItemRepository(session)
        asgn_repo = SQLAlchemyAssignmentRepository(session)
        dec_repo = SQLAlchemyDecisionRepository(session)
        emp_repo = SQLAlchemyEmployeeRepository(session)
        agent_repo = SQLAlchemyAgentRepository(session)
        run_repo = SQLAlchemyAgentRunRepository(session)
        step_repo = SQLAlchemyExecutionStepRepository(session)

        exec_engine = AgentExecutionEngine(
            agent_repo=agent_repo,
            run_repo=run_repo,
            step_repo=step_repo,
            provider_registry=default_provider_registry,
        )

        emp_service = EmployeeService(emp_repo, agent_repo, exec_engine)
        orchestration_service = ManagerOrchestrationService(
            objective_repo=obj_repo,
            plan_repo=plan_repo,
            work_item_repo=wi_repo,
            assignment_repo=asgn_repo,
            decision_repo=dec_repo,
            employee_repo=emp_repo,
            agent_repo=agent_repo,
            execution_engine=exec_engine,
            plan_validator=PlanValidator(),
            employee_selector=EmployeeSelector(),
        )

        # 1. GUARDRAIL 1: Hierarchy Cycle Prevention
        print("\n--- GUARDRAIL 1: Preventing Circular Manager Hierarchy Cycles ---")
        ag_mgr1 = Agent(
            id="ag_m1",
            name="Manager 1",
            role="manager",
            model_configuration=ModelConfiguration("fake", "fake"),
        )
        ag_mgr2 = Agent(
            id="ag_m2",
            name="Manager 2",
            role="manager",
            model_configuration=ModelConfiguration("fake", "fake"),
        )
        ag_mgr3 = Agent(
            id="ag_m3",
            name="Manager 3",
            role="manager",
            model_configuration=ModelConfiguration("fake", "fake"),
        )
        await agent_repo.save(ag_mgr1)
        await agent_repo.save(ag_mgr2)
        await agent_repo.save(ag_mgr3)

        m1 = Employee(
            id="m1",
            employee_code="M1",
            name="Manager 1",
            title="Director",
            role="manager",
            agent_id="ag_m1",
            status=EmployeeStatus.ACTIVE,
        )
        m2 = Employee(
            id="m2",
            employee_code="M2",
            name="Manager 2",
            title="Lead",
            role="manager",
            agent_id="ag_m2",
            status=EmployeeStatus.ACTIVE,
        )
        m3 = Employee(
            id="m3",
            employee_code="M3",
            name="Manager 3",
            title="Lead",
            role="manager",
            agent_id="ag_m3",
            status=EmployeeStatus.ACTIVE,
        )
        await emp_repo.save(m1)
        await emp_repo.save(m2)
        await emp_repo.save(m3)

        await emp_service.update_manager("m2", "m1")
        await emp_service.update_manager("m3", "m2")
        print("[OK] Hierarchy Established: M1 <- M2 <- M3")

        try:
            print(
                "Attempting to assign M3 as M1's manager (Creating Cycle M1 -> M2 -> M3 -> M1)..."
            )
            await emp_service.update_manager("m1", "m3")
        except EmployeeValidationError as exc:
            print(f"[REJECTED EXPECTEDLY] {exc}")

        # 2. GUARDRAIL 2: Non-Manager Plan Proposal Rejection
        print("\n--- GUARDRAIL 2: Preventing Non-Managers from Proposing Plans ---")
        ag_dev = Agent(
            id="ag_dev",
            name="Dev Agent",
            role="developer",
            model_configuration=ModelConfiguration("fake", "fake"),
        )
        await agent_repo.save(ag_dev)

        dev = Employee(
            id="dev1",
            employee_code="D1",
            name="Dev IC",
            title="Junior Software Engineer",
            role="developer",
            agent_id="ag_dev",
            status=EmployeeStatus.ACTIVE,
        )
        await emp_repo.save(dev)

        obj = await orchestration_service.create_objective(
            objective_id="obj_resilience_01",
            title="Refactor Legacy Engine",
            description="Refactor core engine code",
            requester="CTO",
        )

        wi = WorkItem(
            id="wi_1",
            plan_id="p1",
            title="Refactor Module",
            description="Desc",
            required_capabilities=["python"],
        )
        invalid_plan = Plan(id="p1", objective_id=obj.id, manager_id=dev.id, work_items=[wi])

        try:
            print(f"Non-manager {dev.name} ({dev.title}) submitting proposed plan...")
            await orchestration_service.submit_and_validate_plan(invalid_plan)
        except PlanValidationError as exc:
            print(f"[REJECTED EXPECTEDLY] {exc}")

        # 3. GUARDRAIL 3: Capability Mismatch Protection
        print("\n--- GUARDRAIL 3: Capability Mismatch Assignment Protection ---")
        ag_designer = Agent(
            id="ag_des",
            name="Designer Agent",
            role="designer",
            model_configuration=ModelConfiguration("fake", "fake"),
        )
        await agent_repo.save(ag_designer)

        designer = Employee(
            id="des1",
            employee_code="DES1",
            name="UI Specialist",
            title="UX Designer",
            role="designer",
            agent_id="ag_des",
            skills=[EmployeeSkill(name="figma", proficiency=SkillProficiency.EXPERT)],
            status=EmployeeStatus.ACTIVE,
        )
        await emp_repo.save(designer)

        valid_plan = Plan(id="p2", objective_id=obj.id, manager_id=m1.id, work_items=[wi])
        await orchestration_service.submit_and_validate_plan(valid_plan)
        await orchestration_service.approve_plan(valid_plan.id, manager_id=m1.id)

        try:
            print(f"Attempting to assign Python WorkItem 'wi_1' to UX Designer {designer.name}...")
            await orchestration_service.assign_work_item(
                work_item_id="wi_1", employee_id=designer.id, assigned_by_manager_id=m1.id
            )
        except AssignmentError as exc:
            print(f"[REJECTED EXPECTEDLY] {exc}")

        # 4. GUARDRAIL 4: Invalid State Machine Transition Protection
        print("\n--- GUARDRAIL 4: Objective State Machine Protection ---")
        try:
            print(
                "Attempting to transition Objective directly from RECEIVED to COMPLETED..."
            )
            obj.transition_to(ObjectiveStatus.COMPLETED)
        except InvalidStateTransitionError as exc:
            print(f"[REJECTED EXPECTEDLY] {exc}")

        print("=" * 80)
        print("PHASE 3 RESILIENCE & GUARDRAILS DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_resilience_demo())
