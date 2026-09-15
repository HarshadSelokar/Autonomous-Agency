"""
Unit tests for Phase 9 AI Software Company Application Services.
"""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.code_review_service import CodeReviewService
from src.application.qa_service import QAService
from src.application.software_delivery_service import SoftwareDeliveryService
from src.application.software_project_service import SoftwareProjectService
from src.domain.employee import Employee, EmployeeCapability, EmployeeStatus
from src.domain.exceptions import UnauthorizedApprovalError
from src.domain.objective import Objective, ObjectiveStatus
from src.domain.software_company import (
    CodeChange,
    CodeChangeStatus,
    CodeReviewStatus,
    DefectStatus,
    DeliveryStatus,
    SoftwareProject,
    SoftwareProjectStatus,
    TestRunStatus,
)

from src.domain.task import Task, TaskStatus

from src.infrastructure.database import Base
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemyCodeReviewRepository,
    SQLAlchemySoftwareDefectRepository,
    SQLAlchemySoftwareDeliveryRepository,
    SQLAlchemySoftwareProjectRepository,
    SQLAlchemySoftwareRequirementRepository,
    SQLAlchemyTestRunRepository,
)
from src.infrastructure.repositories.task_dependency_repository import SQLAlchemyTaskDependencyRepository
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_software_project_service_workflow(db_session: AsyncSession):
    obj_repo = SQLAlchemyObjectiveRepository(db_session)
    emp_repo = SQLAlchemyEmployeeRepository(db_session)
    proj_repo = SQLAlchemySoftwareProjectRepository(db_session)
    req_repo = SQLAlchemySoftwareRequirementRepository(db_session)
    task_repo = SQLAlchemyTaskRepository(db_session)
    dep_repo = SQLAlchemyTaskDependencyRepository(db_session)

    # 1. Setup Objective & Manager
    objective = await obj_repo.save(
        Objective(id="obj-api", title="Build Customer API", description="REST endpoints for Customer records", requester="CEO")
    )

    mgr = await emp_repo.save(
        Employee(
            id="emp-mgr",
            employee_code="EMP-001",
            name="Alice Manager",
            role="Engineering Manager",
            title="Engineering Director",
            agent_id="agent-mgr",
            capabilities=[EmployeeCapability(name="planning"), EmployeeCapability(name="SOFTWARE_ARCHITECTURE")],
            status=EmployeeStatus.ACTIVE,
        )
    )


    proj_service = SoftwareProjectService(
        project_repo=proj_repo,
        req_repo=req_repo,
        task_repo=task_repo,
        dep_repo=dep_repo,
        employee_repo=emp_repo,
        assignment_repo=None,  # Not directly needed for unit test
        objective_repo=obj_repo,
    )

    # 2. Create Project & Add Requirements
    project = await proj_service.create_software_project(
        objective_id=objective.id,
        name="Customer API Project",
        repository_path="/workspace/customer-api",
    )
    assert project.name == "Customer API Project"

    reqs = await proj_service.add_requirements(
        project_id=project.project_id,
        requirements_data=[
            {
                "title": "POST /customers API",
                "description": "Create new customer",
                "acceptance_criteria": ["201 Created"],
                "priority": "HIGH",
            }
        ],
    )
    assert len(reqs) == 1

    # 3. Create Engineering Plan & Decompose Tasks
    plan = await proj_service.create_engineering_plan(
        project_id=project.project_id,
        manager_employee_id=mgr.id,
        architecture_overview="FastAPI microservice with PostgreSQL backend",
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
    )
    assert len(plan.task_ids) == 4  # Arch, Feature Dev, QA, Review


@pytest.mark.asyncio
async def test_code_review_and_self_approval_protection(db_session: AsyncSession):
    change_repo = SQLAlchemyCodeChangeRepository(db_session)
    review_repo = SQLAlchemyCodeReviewRepository(db_session)
    task_repo = SQLAlchemyTaskRepository(db_session)

    task = await task_repo.save(
        Task(id="task-1", plan_id="plan-1", title="Implement POST /customers", description="Feature Implementation", required_capabilities=["BACKEND_DEVELOPMENT"])
    )


    review_service = CodeReviewService(
        change_repo=change_repo,
        review_repo=review_repo,
        task_repo=task_repo,
    )

    # 1. Submit Code Change
    change = await review_service.submit_code_change(
        project_id="proj-1",
        task_id=task.id,
        author_employee_id="emp-dev-bob",
        files_changed=["app/api/customers.py"],
        diff_summary="+ def create_customer(): return {'id': 1}",
    )
    assert change.status == CodeChangeStatus.PROPOSED

    # 2. Verify Self-Approval Rejection
    with pytest.raises(UnauthorizedApprovalError):
        await review_service.request_code_review(
            change_id=change.change_id,
            reviewer_employee_id="emp-dev-bob",
        )

    # 3. Request Review by Authorized Reviewer
    review = await review_service.request_code_review(
        change_id=change.change_id,
        reviewer_employee_id="emp-reviewer-charlie",
    )
    assert review.status == CodeReviewStatus.PENDING

    # 4. Submit Changes Requested -> Triggers Task Rework
    saved_review, updated_change = await review_service.submit_review_findings(
        review_id=review.review_id,
        status=CodeReviewStatus.CHANGES_REQUESTED,
        findings=["Missing validation on email field"],
    )
    assert updated_change.status == CodeChangeStatus.CHANGES_REQUESTED

    reworked_task = await task_repo.get_by_id(task.id)
    assert reworked_task.retry_count == 1
    assert reworked_task.status == TaskStatus.REWORK



@pytest.mark.asyncio
async def test_qa_service_and_software_delivery_workflow(db_session: AsyncSession):
    proj_repo = SQLAlchemySoftwareProjectRepository(db_session)
    req_repo = SQLAlchemySoftwareRequirementRepository(db_session)
    change_repo = SQLAlchemyCodeChangeRepository(db_session)
    review_repo = SQLAlchemyCodeReviewRepository(db_session)
    test_repo = SQLAlchemyTestRunRepository(db_session)
    defect_repo = SQLAlchemySoftwareDefectRepository(db_session)
    delivery_repo = SQLAlchemySoftwareDeliveryRepository(db_session)
    task_repo = SQLAlchemyTaskRepository(db_session)

    qa_service = QAService(test_repo=test_repo, defect_repo=defect_repo, task_repo=task_repo)
    delivery_service = SoftwareDeliveryService(
        delivery_repo=delivery_repo,
        project_repo=proj_repo,
        req_repo=req_repo,
        change_repo=change_repo,
        test_repo=test_repo,
        defect_repo=defect_repo,
    )

    project = await proj_repo.save(SoftwareProject(name="Delivery Project", objective_id="obj-del"))

    # 1. Record Passing Test Run
    test_run = await qa_service.record_test_run(
        project_id=project.project_id,
        task_id="task-qa",
        worker_employee_id="emp-qa",
        command="pytest tests/",
        exit_code=0,
        total_tests=5,
        passed_count=5,
        failed_count=0,
    )
    assert test_run.status == TestRunStatus.PASSED

    # 2. Add Approved Code Change
    change = await change_repo.save(
        CodeChange(
            project_id=project.project_id,
            task_id="task-dev",
            author_employee_id="emp-dev-bob",
            status=CodeChangeStatus.APPROVED,
        )
    )

    # 3. Request Delivery
    delivery = await delivery_service.request_delivery(
        project_id=project.project_id,
        requested_by_employee_id="emp-dev-bob",
    )

    # 4. Self-approval block check
    with pytest.raises(UnauthorizedApprovalError):
        await delivery_service.approve_delivery(
            delivery_id=delivery.delivery_id,
            approved_by_employee_id="emp-dev-bob",
        )

    # 5. Manager Approve Delivery
    approved_delivery = await delivery_service.approve_delivery(
        delivery_id=delivery.delivery_id,
        approved_by_employee_id="emp-mgr-alice",
    )
    assert approved_delivery.status == DeliveryStatus.DELIVERED
