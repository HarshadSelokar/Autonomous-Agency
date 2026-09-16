"""
Failure-injection tests for Phase 9 AI Software Company workflows.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.code_review_service import CodeReviewService
from src.application.qa_service import QAService
from src.domain.software_company import (
    CodeChangeStatus,
    CodeReviewStatus,
    DefectSeverity,
    DefectStatus,
    TestRunStatus,
)
from src.domain.task import Task, TaskStatus
from src.infrastructure.database import Base
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemyCodeReviewRepository,
    SQLAlchemySoftwareDefectRepository,
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
async def test_failing_test_run_execution(db_session: AsyncSession):
    test_repo = SQLAlchemyTestRunRepository(db_session)
    defect_repo = SQLAlchemySoftwareDefectRepository(db_session)
    task_repo = SQLAlchemyTaskRepository(db_session)

    qa_service = QAService(test_repo=test_repo, defect_repo=defect_repo, task_repo=task_repo)

    # 1. Record Failing Test Run (non-zero exit code, failed_count > 0)
    test_run = await qa_service.record_test_run(
        project_id="proj-fail",
        task_id="task-fail-1",
        worker_employee_id="emp-qa",
        command="pytest tests/unit",
        exit_code=1,
        total_tests=10,
        passed_count=8,
        failed_count=2,
        output_reference="2 tests failed with AssertionError",
    )
    assert test_run.status == TestRunStatus.FAILED
    assert test_run.exit_code == 1


@pytest.mark.asyncio
async def test_code_review_rejection_task_rework_trigger(db_session: AsyncSession):
    change_repo = SQLAlchemyCodeChangeRepository(db_session)
    review_repo = SQLAlchemyCodeReviewRepository(db_session)
    task_repo = SQLAlchemyTaskRepository(db_session)

    task = await task_repo.save(
        Task(id="task-dev-1", plan_id="plan-1", title="Feature Task", description="Feature Implementation", required_capabilities=["BACKEND_DEVELOPMENT"])
    )

    review_service = CodeReviewService(change_repo=change_repo, review_repo=review_repo, task_repo=task_repo)

    change = await review_service.submit_code_change(
        project_id="proj-rework",
        task_id=task.id,
        author_employee_id="emp-author-dev",
        files_changed=["app/api.py"],
        diff_summary="+ buggy feature",
    )

    review = await review_service.request_code_review(
        change_id=change.change_id,
        reviewer_employee_id="emp-reviewer-lead",
    )

    # Submit CHANGES_REQUESTED -> Triggers Task REWORK
    saved_review, updated_change = await review_service.submit_review_findings(
        review_id=review.review_id,
        status=CodeReviewStatus.CHANGES_REQUESTED,
        findings=["Memory leak in buffer allocation", "Missing unit tests"],
    )

    assert updated_change.status == CodeChangeStatus.CHANGES_REQUESTED
    reworked_task = await task_repo.get_by_id(task.id)
    assert reworked_task.retry_count == 1
    assert reworked_task.status == TaskStatus.REWORK


@pytest.mark.asyncio
async def test_defect_fix_verification_failure_handling(db_session: AsyncSession):
    test_repo = SQLAlchemyTestRunRepository(db_session)
    defect_repo = SQLAlchemySoftwareDefectRepository(db_session)
    task_repo = SQLAlchemyTaskRepository(db_session)

    qa_service = QAService(test_repo=test_repo, defect_repo=defect_repo, task_repo=task_repo)

    defect, fix_task = await qa_service.report_defect(
        project_id="proj-bug",
        title="Database lock timeout under heavy load",
        severity=DefectSeverity.HIGH,
    )
    assert defect.status == DefectStatus.OPEN
    assert fix_task.id is not None

    # Failed verification test run
    failed_test = await qa_service.record_test_run(
        project_id="proj-bug",
        task_id=fix_task.id,
        worker_employee_id="emp-qa",
        command="pytest tests/load",
        exit_code=1,
        total_tests=5,
        passed_count=4,
        failed_count=1,
    )

    # Verifying defect with a failed test run must raise ValueError
    with pytest.raises(ValueError, match="failed"):
        await qa_service.verify_defect_fix(
            defect_id=defect.defect_id,
            verification_test_run_id=failed_test.test_run_id,
        )
