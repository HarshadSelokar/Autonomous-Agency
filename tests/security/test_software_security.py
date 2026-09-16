"""
Security tests for Phase 9 AI Software Company boundaries, self-approval guards, and release governance.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.code_review_service import CodeReviewService
from src.application.qa_service import QAService
from src.application.software_delivery_service import SoftwareDeliveryService
from src.domain.exceptions import UnauthorizedApprovalError
from src.domain.software_company import (
    DefectSeverity,
    SoftwareProject,
)
from src.domain.task import Task
from src.infrastructure.database import Base
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemyCodeReviewRepository,
    SQLAlchemySoftwareDefectRepository,
    SQLAlchemySoftwareDeliveryRepository,
    SQLAlchemySoftwareProjectRepository,
    SQLAlchemySoftwareRequirementRepository,
    SQLAlchemyTestRunRepository,
)
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
async def test_code_review_self_approval_blocked(db_session: AsyncSession):
    change_repo = SQLAlchemyCodeChangeRepository(db_session)
    review_repo = SQLAlchemyCodeReviewRepository(db_session)
    task_repo = SQLAlchemyTaskRepository(db_session)

    task = await task_repo.save(
        Task(id="t-sec-1", plan_id="plan-sec", title="Security Feature", description="Sec feature", required_capabilities=["BACKEND_DEVELOPMENT"])
    )

    service = CodeReviewService(change_repo=change_repo, review_repo=review_repo, task_repo=task_repo)

    change = await service.submit_code_change(
        project_id="proj-sec",
        task_id=task.id,
        author_employee_id="emp-author-alice",
        files_changed=["sec.py"],
        diff_summary="+ sec",
    )

    # Rejection of author reviewing their own code
    with pytest.raises(UnauthorizedApprovalError):
        await service.request_code_review(change_id=change.change_id, reviewer_employee_id="emp-author-alice")


@pytest.mark.asyncio
async def test_delivery_self_approval_blocked(db_session: AsyncSession):
    delivery_repo = SQLAlchemySoftwareDeliveryRepository(db_session)
    proj_repo = SQLAlchemySoftwareProjectRepository(db_session)
    req_repo = SQLAlchemySoftwareRequirementRepository(db_session)
    change_repo = SQLAlchemyCodeChangeRepository(db_session)
    test_repo = SQLAlchemyTestRunRepository(db_session)
    defect_repo = SQLAlchemySoftwareDefectRepository(db_session)

    service = SoftwareDeliveryService(
        delivery_repo=delivery_repo,
        project_repo=proj_repo,
        req_repo=req_repo,
        change_repo=change_repo,
        test_repo=test_repo,
        defect_repo=defect_repo,
    )

    project = await proj_repo.save(SoftwareProject(name="Sec Delivery", objective_id="obj-sec"))
    delivery = await service.request_delivery(project_id=project.project_id, requested_by_employee_id="emp-dev-bob")

    with pytest.raises(UnauthorizedApprovalError):
        await service.approve_delivery(delivery_id=delivery.delivery_id, approved_by_employee_id="emp-dev-bob")


@pytest.mark.asyncio
async def test_delivery_blocked_by_open_defects(db_session: AsyncSession):
    delivery_repo = SQLAlchemySoftwareDeliveryRepository(db_session)
    proj_repo = SQLAlchemySoftwareProjectRepository(db_session)
    req_repo = SQLAlchemySoftwareRequirementRepository(db_session)
    change_repo = SQLAlchemyCodeChangeRepository(db_session)
    test_repo = SQLAlchemyTestRunRepository(db_session)
    defect_repo = SQLAlchemySoftwareDefectRepository(db_session)
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

    project = await proj_repo.save(SoftwareProject(name="Defect Delivery", objective_id="obj-def"))

    # Add passing test
    await qa_service.record_test_run(
        project_id=project.project_id,
        task_id="t-1",
        worker_employee_id="emp-qa",
        command="pytest",
        exit_code=0,
        total_tests=1,
        passed_count=1,
        failed_count=0,
    )

    # Report unresolved defect
    await qa_service.report_defect(
        project_id=project.project_id,
        title="Critical Security Hole",
        severity=DefectSeverity.CRITICAL,
    )

    delivery = await delivery_service.request_delivery(
        project_id=project.project_id, requested_by_employee_id="emp-dev-bob"
    )

    # Attempting manager approval should raise ValueError due to open defect
    with pytest.raises(ValueError, match="unresolved defects"):
        await delivery_service.approve_delivery(
            delivery_id=delivery.delivery_id, approved_by_employee_id="emp-mgr-alice"
        )
