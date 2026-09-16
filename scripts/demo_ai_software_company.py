"""
End-to-End Demonstration Script for Phase 9 — AI Software Company.

Demonstrates:
1. Software Objective -> Engineering Manager Analysis -> Requirements -> Engineering Plan -> Task Decomposition.
2. Capability-based employee assignment (Manager, Developer, QA Engineer).
3. Code change submission, code review approval, and self-approval protection block.
4. Tool-based test run execution and evidence recording.
5. Release delivery approval & evidence verification.
6. Defect logging, bugfix task generation, and verified defect fix workflow.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.code_review_service import CodeReviewService
from src.application.qa_service import QAService
from src.application.software_delivery_service import SoftwareDeliveryService
from src.application.software_project_service import SoftwareProjectService
from src.domain.employee import Employee, EmployeeCapability, EmployeeStatus
from src.domain.exceptions import UnauthorizedApprovalError
from src.domain.objective import Objective
from src.domain.software_company import (
    CodeReviewStatus,
    DefectSeverity,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.assignment_repository import SQLAlchemyAssignmentRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemyCodeReviewRepository,
    SQLAlchemyEngineeringPlanRepository,
    SQLAlchemySoftwareDefectRepository,
    SQLAlchemySoftwareDeliveryRepository,
    SQLAlchemySoftwareProjectRepository,
    SQLAlchemySoftwareRequirementRepository,
    SQLAlchemyTestRunRepository,
)
from src.infrastructure.repositories.task_dependency_repository import (
    SQLAlchemyTaskDependencyRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


async def run_demo():
    print("=" * 80)
    print("PHASE 9 — AI SOFTWARE COMPANY END-TO-END DEMONSTRATION")
    print("=" * 80)

    # 1. Setup In-Memory Database Engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Repositories
        obj_repo = SQLAlchemyObjectiveRepository(session)
        emp_repo = SQLAlchemyEmployeeRepository(session)
        proj_repo = SQLAlchemySoftwareProjectRepository(session)
        req_repo = SQLAlchemySoftwareRequirementRepository(session)
        plan_repo = SQLAlchemyEngineeringPlanRepository(session)
        task_repo = SQLAlchemyTaskRepository(session)
        dep_repo = SQLAlchemyTaskDependencyRepository(session)
        asgn_repo = SQLAlchemyAssignmentRepository(session)
        change_repo = SQLAlchemyCodeChangeRepository(session)
        review_repo = SQLAlchemyCodeReviewRepository(session)
        test_repo = SQLAlchemyTestRunRepository(session)
        defect_repo = SQLAlchemySoftwareDefectRepository(session)
        delivery_repo = SQLAlchemySoftwareDeliveryRepository(session)

        # Services
        proj_service = SoftwareProjectService(
            project_repo=proj_repo,
            req_repo=req_repo,
            task_repo=task_repo,
            dep_repo=dep_repo,
            employee_repo=emp_repo,
            assignment_repo=asgn_repo,
            objective_repo=obj_repo,
            plan_repo=plan_repo,
            change_repo=change_repo,
            test_repo=test_repo,
            defect_repo=defect_repo,
        )
        review_service = CodeReviewService(
            change_repo=change_repo,
            review_repo=review_repo,
            task_repo=task_repo,
        )
        qa_service = QAService(
            test_repo=test_repo,
            defect_repo=defect_repo,
            task_repo=task_repo,
        )
        delivery_service = SoftwareDeliveryService(
            delivery_repo=delivery_repo,
            project_repo=proj_repo,
            req_repo=req_repo,
            change_repo=change_repo,
            test_repo=test_repo,
            defect_repo=defect_repo,
        )

        print("\n--- STEP 1: INITIALIZING AI SOFTWARE COMPANY ORGANIZATIONAL STRUCTURE ---")
        objective = await obj_repo.save(
            Objective(
                id="obj-customer-api",
                title="Build Customer Management REST API",
                description="Develop a high-performance REST microservice for customer onboarding and retrieval.",
                requester="Chief Technology Officer",
            )
        )
        print(f"Objective Created: '{objective.title}' (ID: {objective.id})")

        mgr_alice = await emp_repo.save(
            Employee(
                id="emp-mgr-alice",
                employee_code="EMP-MGR-01",
                name="Alice Vance",
                title="Engineering Manager",
                role="Manager",
                agent_id="agent-mgr-alice",
                capabilities=[
                    EmployeeCapability(name="planning"),
                    EmployeeCapability(name="SOFTWARE_ARCHITECTURE"),
                    EmployeeCapability(name="CODE_REVIEW"),
                ],
                status=EmployeeStatus.ACTIVE,
            )
        )
        dev_bob = await emp_repo.save(
            Employee(
                id="emp-dev-bob",
                employee_code="EMP-DEV-01",
                name="Bob Builder",
                title="Senior Backend Engineer",
                role="Software Developer",
                agent_id="agent-dev-bob",
                capabilities=[EmployeeCapability(name="BACKEND_DEVELOPMENT")],
                status=EmployeeStatus.ACTIVE,
            )
        )
        qa_charlie = await emp_repo.save(
            Employee(
                id="emp-qa-charlie",
                employee_code="EMP-QA-01",
                name="Charlie Tester",
                title="QA Engineer",
                role="QA Engineer",
                agent_id="agent-qa-charlie",
                capabilities=[
                    EmployeeCapability(name="QA_ENGINEERING"),
                    EmployeeCapability(name="CODE_REVIEW"),
                ],
                status=EmployeeStatus.ACTIVE,
            )
        )
        print(f"AI Employees Initialized:\n  - Manager: {mgr_alice.name}\n  - Developer: {dev_bob.name}\n  - QA Engineer: {qa_charlie.name}")

        print("\n--- STEP 2: CREATING SOFTWARE PROJECT & ANALYZING REQUIREMENTS ---")
        project = await proj_service.create_software_project(
            objective_id=objective.id,
            name="Customer Microservice API",
            description="REST microservice handling customer CRUD operations.",
            repository_path="/workspaces/customer-api",
        )
        print(f"Software Project Created: '{project.name}' (Status: {project.status.value})")

        requirements = await proj_service.add_requirements(
            project_id=project.project_id,
            requirements_data=[
                {
                    "title": "POST /customers Onboarding Endpoint",
                    "description": "Accept customer details and return 201 Created.",
                    "acceptance_criteria": ["201 Created on valid payload", "400 Bad Request on invalid email"],
                    "priority": "HIGH",
                },
                {
                    "title": "GET /customers/{id} Lookup Endpoint",
                    "description": "Retrieve customer by ID.",
                    "acceptance_criteria": ["200 OK with customer record", "404 Not Found if missing"],
                    "priority": "HIGH",
                },
            ],
        )
        print(f"Requirements Analyzed & Created: {len(requirements)} items.")

        print("\n--- STEP 3: ENGINEERING MANAGER DECOMPOSING TASK GRAPH ---")
        plan = await proj_service.create_engineering_plan(
            project_id=project.project_id,
            manager_employee_id=mgr_alice.id,
            architecture_overview="FastAPI REST API with SQLite/PostgreSQL storage.",
            tech_stack=["Python", "FastAPI", "SQLAlchemy", "Pytest"],
        )
        print(f"Engineering Plan Created: {len(plan.task_ids)} tasks in DAG execution graph.")

        assignments = await proj_service.assign_engineering_tasks(project.project_id)
        print(f"Capability-based Task Assignments Complete: Assigned {len(assignments)} tasks.")

        print("\n--- STEP 4: DEVELOPER IMPLEMENTATION & CODE CHANGE SUBMISSION ---")
        change = await review_service.submit_code_change(
            project_id=project.project_id,
            task_id=plan.task_ids[1],
            author_employee_id=dev_bob.id,
            files_changed=["app/api/customers.py", "app/models/customer.py"],
            diff_summary="+ class CustomerModel(Base):\n+ @router.post('/customers')",
            branch_name="feature/customer-endpoints",
        )
        print(f"CodeChange Submitted: ID '{change.change_id}' by {dev_bob.name} (Status: {change.status.value})")

        print("\n--- STEP 5: CODE REVIEW & SELF-APPROVAL GUARD TESTING ---")
        print(f"Attempting self-approval by Author {dev_bob.name}...")
        try:
            await review_service.request_code_review(
                change_id=change.change_id,
                reviewer_employee_id=dev_bob.id,
            )
            print("ERROR: Self-approval allowed unexpectedly!")
        except UnauthorizedApprovalError as err:
            print(f"  SAFETY GUARD VERIFIED: {err}")

        print(f"\nRequesting Code Review from QA/Reviewer {qa_charlie.name}...")
        review = await review_service.request_code_review(
            change_id=change.change_id,
            reviewer_employee_id=qa_charlie.id,
        )
        print(f"CodeReview Initialized (Status: {review.status.value})")

        saved_review, approved_change = await review_service.submit_review_findings(
            review_id=review.review_id,
            status=CodeReviewStatus.APPROVED,
            findings=["Code structure is clean", "Type annotations verified"],
            recommendations="Ready for QA execution",
        )
        print(f"CodeReview Approved by {qa_charlie.name}. Change Status: {approved_change.status.value}")

        print("\n--- STEP 6: TOOL-BASED TEST EXECUTION & EVIDENCE RECORDING ---")
        test_run = await qa_service.record_test_run(
            project_id=project.project_id,
            task_id=plan.task_ids[2],
            worker_employee_id=qa_charlie.id,
            command="pytest tests/unit/test_customers.py",
            exit_code=0,
            total_tests=6,
            passed_count=6,
            failed_count=0,
            output_reference="6 passed in 0.12s",
        )
        print(f"TestRun Executed via Tool: Exit Code {test_run.exit_code}, Status: {test_run.status.value} (6/6 Passed)")

        print("\n--- STEP 7: DEFECT WORKFLOW DEMONSTRATION ---")
        defect, fix_task = await qa_service.report_defect(
            project_id=project.project_id,
            title="Duplicate email check fails under heavy load",
            severity=DefectSeverity.HIGH,
            reproduction_steps="Submit concurrent POST /customers with same email",
            originating_task_id=plan.task_ids[2],
            assigned_employee_id=dev_bob.id,
        )
        print(f"Software Defect Logged: '{defect.title}' (Severity: {defect.severity.value})")
        print(f"  Bugfix Task Generated in Task Engine: '{fix_task.title}' (Status: {fix_task.status.value})")

        # Developer fixes and QA re-verifies with passing test
        verify_test = await qa_service.record_test_run(
            project_id=project.project_id,
            task_id=fix_task.id,
            worker_employee_id=qa_charlie.id,
            command="pytest tests/integration/test_concurrency.py",
            exit_code=0,
            total_tests=2,
            passed_count=2,
            failed_count=0,
        )
        closed_defect = await qa_service.verify_defect_fix(
            defect_id=defect.defect_id,
            verification_test_run_id=verify_test.test_run_id,
        )
        print(f"Defect Verified & Closed using Test Run '{verify_test.test_run_id}'. Status: {closed_defect.status.value}")

        print("\n--- STEP 8: RELEASE DELIVERY APPROVAL & EVIDENCE VERIFICATION ---")
        delivery = await delivery_service.request_delivery(
            project_id=project.project_id,
            requested_by_employee_id=dev_bob.id,
            version="1.0.0",
            commit_hash="c0ff33a11b",
        )
        print(f"Release Delivery Requested by {dev_bob.name} (Status: {delivery.status.value})")

        approved_delivery = await delivery_service.approve_delivery(
            delivery_id=delivery.delivery_id,
            approved_by_employee_id=mgr_alice.id,
        )
        print(f"Software Delivery Approved by Manager {mgr_alice.name}!")
        print(f"  Final Delivery Status: {approved_delivery.status.value}")
        print(f"  Evidence Summary: {approved_delivery.evidence_summary}")

        print("\n--- STEP 9: PROJECT STATUS METRICS SUMMARY ---")
        status_metrics = await proj_service.get_project_status(project.project_id)
        for k, v in status_metrics.items():
            print(f"  - {k}: {v}")

        await session.commit()

    print("\n" + "=" * 80)
    print("PHASE 9 E2E DEMONSTRATION PASSED PERFECTLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())
