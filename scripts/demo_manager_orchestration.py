"""
Phase 3 Demonstration Script — Manager & Organizational Orchestration.

Demonstrates full end-to-end Phase 3 orchestration flow:
Objective Creation -> Ambiguity Clarification -> Manager Plan Submission ->
Plan Validation & Approval -> Capability-Based Work Item Assignment ->
Blocker Escalation & Reassignment -> Work Execution -> Objective Completion.
"""

import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.employee_selector import EmployeeSelector
from src.application.execution_engine import AgentExecutionEngine
from src.application.manager_orchestration_service import ManagerOrchestrationService
from src.application.plan_validator import PlanValidator
from src.application.provider_registry import default_provider_registry
from src.domain.agent import Agent, ModelConfiguration
from src.domain.employee import (
    Employee,
    EmployeeCapability,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)
from src.domain.objective import ObjectiveStatus
from src.domain.plan import Plan
from src.domain.work_item import WorkItem, WorkItemStatus
from src.infrastructure.config import settings
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.providers.groq_provider import GroqModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.assignment_repository import SQLAlchemyAssignmentRepository
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
from src.infrastructure.repositories.plan_repository import SQLAlchemyPlanRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository
from src.infrastructure.repositories.work_item_repository import SQLAlchemyWorkItemRepository


async def run_demo() -> None:
    print("=" * 80)
    print("AUTONOMOUS AI COMPANY PLATFORM - PHASE 3 MANAGER ORCHESTRATION DEMO")
    print("=" * 80)

    # 1. Database Setup
    db_url = os.environ.get(
        "DEMO_DATABASE_URL", "sqlite+aiosqlite:///manager_orchestration_demo.db"
    )
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Provider Setup
    groq_api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        print("[SETUP] Groq API key detected. Using live GroqModelProvider.")
        default_provider_registry.register(GroqModelProvider(api_key=groq_api_key))
    else:
        print("[SETUP] GROQ_API_KEY not configured. Using deterministic FakeModelProvider.")
        default_provider_registry.register(
            FakeModelProvider(
                canned_content=(
                    "ORCHESTRATION PLAN: Deconstruct objective into backend, processing, and "
                    "frontend work items."
                )
            )
        )

    async with session_factory() as session:
        # Repositories
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

        # 3. Provision Organizational Workforce
        print("\n--- STEP 1: Provisioning Organizational Workforce ---")

        # Manager Agent & Employee
        mgr_agent = Agent(
            id="ag_alice_mgr",
            name="Alice Manager Agent",
            role="Engineering Lead",
            model_configuration=ModelConfiguration(
                provider="groq" if groq_api_key else "fake",
                model="llama-3.3-70b-versatile" if groq_api_key else "fake-model",
            ),
        )
        await agent_repo.save(mgr_agent)

        alice = Employee(
            id="emp_alice_mgr",
            employee_code="EMP-MGR-01",
            name="Alice Vance",
            title="Engineering Manager",
            role="manager",
            agent_id="ag_alice_mgr",
            capabilities=[
                EmployeeCapability(name="planning"),
                EmployeeCapability(name="task_decomposition"),
            ],
            status=EmployeeStatus.ACTIVE,
        )
        await emp_repo.save(alice)
        print(f"[OK] Provisioned Manager: {alice.name} ({alice.title})")

        # Backend Developer Agent & Employee
        bob_agent = Agent(
            id="ag_bob_dev",
            name="Bob Developer Agent",
            role="Backend Engineer",
            model_configuration=ModelConfiguration(
                provider="groq" if groq_api_key else "fake",
                model="llama-3.3-70b-versatile" if groq_api_key else "fake-model",
            ),
        )
        await agent_repo.save(bob_agent)

        bob = Employee(
            id="emp_bob_dev",
            employee_code="EMP-DEV-01",
            name="Bob Smith",
            title="Senior Software Engineer",
            role="developer",
            agent_id="ag_bob_dev",
            skills=[
                EmployeeSkill(name="python", proficiency=SkillProficiency.EXPERT),
                EmployeeSkill(name="fastapi", proficiency=SkillProficiency.ADVANCED),
                EmployeeSkill(name="pandas", proficiency=SkillProficiency.EXPERT),
            ],
            status=EmployeeStatus.ACTIVE,
        )
        await emp_repo.save(bob)
        print(f"[OK] Provisioned Employee: {bob.name} ({bob.title})")

        # Frontend Developer Agent & Employee
        charlie_agent = Agent(
            id="ag_charlie_ui",
            name="Charlie UI Agent",
            role="UI/UX Engineer",
            model_configuration=ModelConfiguration(
                provider="groq" if groq_api_key else "fake",
                model="llama-3.3-70b-versatile" if groq_api_key else "fake-model",
            ),
        )
        await agent_repo.save(charlie_agent)

        charlie = Employee(
            id="emp_charlie_ui",
            employee_code="EMP-UI-01",
            name="Charlie Brown",
            title="Frontend Developer",
            role="developer",
            agent_id="ag_charlie_ui",
            skills=[
                EmployeeSkill(name="python", proficiency=SkillProficiency.INTERMEDIATE),
                EmployeeSkill(name="ui", proficiency=SkillProficiency.EXPERT),
                EmployeeSkill(name="html", proficiency=SkillProficiency.EXPERT),
            ],
            status=EmployeeStatus.ACTIVE,
        )
        await emp_repo.save(charlie)
        print(f"[OK] Provisioned Employee: {charlie.name} ({charlie.title})")

        # 4. Create Organizational Objective
        print("\n--- STEP 2: Submitting Corporate Objective ---")
        obj = await orchestration_service.create_objective(
            objective_id="obj_csv_analytics_2026",
            title="Build Corporate CSV Data Analytics & Visualization Tool",
            description=(
                "Develop a Python web application that parses financial CSV files, "
                "computes analytical metrics, and renders data visualization dashboards."
            ),
            requester="Chief Technology Officer",
            priority="high",
            constraints=["python3.11", "fastapi", "pandas"],
            manager_id=alice.id,
        )
        print(f"[OK] Objective Created: [{obj.id}] {obj.title} (Status: {obj.status.value})")

        # 5. Ambiguity Clarification Cycle
        print("\n--- STEP 3: Manager Ambiguity Clarification Flow ---")
        obj_clarify = await orchestration_service.request_clarification(
            objective_id=obj.id,
            questions=[
                "What max CSV payload size should be supported?",
                "Must dashboard export PDF reports?",
            ],
        )
        print(f"[OK] Clarification Requested: Status -> {obj_clarify.status.value}")

        obj_ready = await orchestration_service.provide_clarification(
            objective_id=obj.id,
            answers={
                "What max CSV payload size should be supported?": "Up to 50MB files.",
                "Must dashboard export PDF reports?": "Optional in V1, HTML charts required.",
            },
        )
        print(f"[OK] Clarification Provided: Status -> {obj_ready.status.value}")

        # 6. Manager Proposes & Validates Plan
        print("\n--- STEP 4: Manager Proposing & Validating Decomposition Plan ---")
        wi1 = WorkItem(
            id="wi_arch_api",
            plan_id="plan_csv_v1",
            title="REST API Architecture & Endpoint Definitions",
            description="Design FastAPI routes for CSV file upload and analytics query endpoints.",
            required_capabilities=["python", "fastapi"],
            priority="high",
        )
        wi2 = WorkItem(
            id="wi_pandas_engine",
            plan_id="plan_csv_v1",
            title="Pandas Data Analysis & Ingestion Engine",
            description=(
                "Build robust CSV ingestion parser, data cleaner, and aggregations using Pandas."
            ),
            required_capabilities=["python", "pandas"],
            priority="high",
        )
        wi3 = WorkItem(
            id="wi_dashboard_ui",
            plan_id="plan_csv_v1",
            title="HTML/CSS Interactive Dashboard UI",
            description=(
                "Create responsive frontend visualization dashboard displaying analytical metrics."
            ),
            required_capabilities=["python", "ui"],
            priority="medium",
        )

        proposed_plan = Plan(
            id="plan_csv_v1",
            objective_id=obj.id,
            manager_id=alice.id,
            goals=["High performance CSV parsing", "Responsive analytics UI"],
            work_items=[wi1, wi2, wi3],
            assumptions=["CSV formatted according to standard UTF-8 headers"],
            risks=["Large CSV files memory overhead"],
        )

        saved_plan, obj_planned = await orchestration_service.submit_and_validate_plan(
            proposed_plan
        )
        print(
            f"[OK] Plan Submitted: {saved_plan.id} with {len(saved_plan.work_items)} WorkItems "
            f"(Status: {saved_plan.status.value})"
        )
        print(f"[OK] Objective Status: -> {obj_planned.status.value}")

        # 7. Approve Plan
        print("\n--- STEP 5: Manager Approving Plan & Initiating Execution ---")
        approved_plan = await orchestration_service.approve_plan(saved_plan.id, manager_id=alice.id)
        exec_obj = await orchestration_service.get_objective(obj.id)
        print(f"[OK] Plan Approved: Status -> {approved_plan.status.value}")
        print(f"[OK] Objective Status: -> {exec_obj.status.value}")

        # 8. Work Item Capability-Based Assignments
        print("\n--- STEP 6: Capability-Based Work Item Allocation ---")
        await orchestration_service.assign_work_item(
            work_item_id=wi1.id,
            employee_id=bob.id,
            assigned_by_manager_id=alice.id,
            reason="Bob is Expert in Python and FastAPI",
        )
        print(f"[OK] Assigned WorkItem '{wi1.title}' -> Employee {bob.name}")

        await orchestration_service.assign_work_item(
            work_item_id=wi2.id,
            employee_id=bob.id,
            assigned_by_manager_id=alice.id,
            reason="Bob is Expert in Pandas",
        )
        print(f"[OK] Assigned WorkItem '{wi2.title}' -> Employee {bob.name}")

        await orchestration_service.assign_work_item(
            work_item_id=wi3.id,
            employee_id=charlie.id,
            assigned_by_manager_id=alice.id,
            reason="Charlie is Expert in UI",
        )
        print(f"[OK] Assigned WorkItem '{wi3.title}' -> Employee {charlie.name}")

        # 9. Blocker Escalation and Resolution
        print("\n--- STEP 7: Simulating Blocker Escalation & Manager Reassignment ---")
        blocked_wi2 = await orchestration_service.handle_blocker(
            work_item_id=wi2.id,
            objective_id=obj.id,
            employee_id=bob.id,
            reason="Sample CSV dataset schema definitions unavailable for Pandas unit test cases.",
        )
        print(f"[WARN] Blocker Logged on WorkItem [{wi2.id}]: Status -> {blocked_wi2.status.value}")

        reassigned_asgn2 = await orchestration_service.reassign_work_item(
            work_item_id=wi2.id,
            new_employee_id=bob.id,
            assigned_by_manager_id=alice.id,
            reason="Manager provided sample CSV schema definitions and re-authorized execution.",
        )
        print(
            f"[OK] Blocker Resolved by Manager: WorkItem [{wi2.id}] -> "
            f"Status: {reassigned_asgn2.status.value}"
        )

        # 10. Simulating Execution & Objective Completion
        print("\n--- STEP 8: Work Execution & Objective Completion ---")
        # Mark work items completed
        for wi in [wi1, wi2, wi3]:
            item = await wi_repo.get_by_id(wi.id)
            if item:
                item.status = WorkItemStatus.COMPLETED
                item.result = {"summary": f"Successfully completed {item.title}"}
                await wi_repo.save(item)

        # Transition objective through REVIEWING to COMPLETED
        exec_obj.transition_to(ObjectiveStatus.REVIEWING)
        exec_obj.transition_to(ObjectiveStatus.COMPLETED)
        await obj_repo.save(exec_obj)

        final_obj = await orchestration_service.get_objective(obj.id)
        print("[OK] All WorkItems Executed & Verified!")
        print(f"[OK] FINAL OBJECTIVE STATUS: [{final_obj.id}] -> {final_obj.status.value}")
        print("=" * 80)
        print("PHASE 3 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())
