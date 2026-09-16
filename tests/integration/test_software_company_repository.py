"""
Integration tests for Phase 9 SQLAlchemy Software Company Repositories.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.software_company import (
    CodeChange,
    DefectSeverity,
    DefectStatus,
    DeliveryStatus,
    RequirementPriority,
    SoftwareDefect,
    SoftwareDelivery,
    SoftwareProject,
    SoftwareProjectStatus,
    SoftwareRequirement,
    TestRun,
    TestRunStatus,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemySoftwareDefectRepository,
    SQLAlchemySoftwareDeliveryRepository,
    SQLAlchemySoftwareProjectRepository,
    SQLAlchemySoftwareRequirementRepository,
    SQLAlchemyTestRunRepository,
)


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
async def test_software_project_repository_flow(db_session: AsyncSession):
    proj_repo = SQLAlchemySoftwareProjectRepository(db_session)

    project = SoftwareProject(
        name="Customer API Engine",
        objective_id="obj-001",
        repository_path="/repos/customer-api",
        status=SoftwareProjectStatus.CREATED,
    )
    saved = await proj_repo.save(project)
    assert saved.name == "Customer API Engine"

    retrieved = await proj_repo.get_by_id(saved.project_id)
    assert retrieved is not None
    assert retrieved.name == "Customer API Engine"
    assert retrieved.status == SoftwareProjectStatus.CREATED

    by_obj = await proj_repo.get_by_objective_id("obj-001")
    assert by_obj is not None
    assert by_obj.project_id == saved.project_id


@pytest.mark.asyncio
async def test_software_requirement_and_code_change_repositories(db_session: AsyncSession):
    proj_repo = SQLAlchemySoftwareProjectRepository(db_session)
    req_repo = SQLAlchemySoftwareRequirementRepository(db_session)
    change_repo = SQLAlchemyCodeChangeRepository(db_session)

    project = await proj_repo.save(
        SoftwareProject(name="E-Commerce System", objective_id="obj-002", repository_path="/repos/shop")
    )

    req = await req_repo.save(
        SoftwareRequirement(
            project_id=project.project_id,
            title="Cart Checkout API",
            acceptance_criteria=["Return 200 OK on checkout"],
            priority=RequirementPriority.HIGH,
        )
    )
    assert req.requirement_id is not None

    reqs = await req_repo.list_by_project(project.project_id)
    assert len(reqs) == 1
    assert reqs[0].title == "Cart Checkout API"

    change = await change_repo.save(
        CodeChange(
            project_id=project.project_id,
            task_id="task-100",
            author_employee_id="emp-dev-1",
            branch_name="feature/checkout",
            files_changed=["cart.py"],
        )
    )
    retrieved_change = await change_repo.get_by_id(change.change_id)
    assert retrieved_change is not None
    assert retrieved_change.branch_name == "feature/checkout"


@pytest.mark.asyncio
async def test_code_review_and_test_run_repositories(db_session: AsyncSession):
    test_repo = SQLAlchemyTestRunRepository(db_session)
    defect_repo = SQLAlchemySoftwareDefectRepository(db_session)
    delivery_repo = SQLAlchemySoftwareDeliveryRepository(db_session)

    test_run = await test_repo.save(
        TestRun(
            project_id="proj-999",
            task_id="task-999",
            worker_employee_id="emp-qa",
            command="pytest tests/",
            exit_code=0,
            total_tests=10,
            passed_count=10,
            status=TestRunStatus.PASSED,
        )
    )
    retrieved_test = await test_repo.get_by_id(test_run.test_run_id)
    assert retrieved_test is not None
    assert retrieved_test.passed_count == 10

    defect = await defect_repo.save(
        SoftwareDefect(
            project_id="proj-999",
            title="Broken checkout button",
            severity=DefectSeverity.CRITICAL,
            status=DefectStatus.OPEN,
        )
    )
    retrieved_defect = await defect_repo.get_by_id(defect.defect_id)
    assert retrieved_defect is not None
    assert retrieved_defect.severity == DefectSeverity.CRITICAL

    delivery = await delivery_repo.save(
        SoftwareDelivery(
            project_id="proj-999",
            version="1.0.0",
            requested_by_employee_id="emp-dev",
            status=DeliveryStatus.DRAFT,
        )
    )
    retrieved_del = await delivery_repo.get_by_id(delivery.delivery_id)
    assert retrieved_del is not None
    assert retrieved_del.version == "1.0.0"
