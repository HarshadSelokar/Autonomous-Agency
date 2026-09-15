"""Integration tests for Department & Cross-Department repositories."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.department import Department, DepartmentStatus
from src.domain.cross_department import (
    DepartmentHandoff,
    DepartmentPriority,
    DepartmentRequest,
    DepartmentRequestStatus,
    HandoffStatus,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository
from src.infrastructure.repositories.cross_department_repository import (
    SQLAlchemyDepartmentHandoffRepository,
    SQLAlchemyDepartmentRequestRepository,
)


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_department_repository_crud(db_session):
    repo = SQLAlchemyDepartmentRepository(db_session)

    dept = Department(
        id="dept-mkt",
        name="Marketing",
        code="MKT",
        description="Marketing and Content",
        status=DepartmentStatus.ACTIVE,
        purpose="Drive awareness and campaigns",
        capabilities=["MARKET_RESEARCH", "CONTENT_CREATION"],
    )

    saved = await repo.save(dept)
    assert saved.id == "dept-mkt"
    assert saved.capabilities == ["MARKET_RESEARCH", "CONTENT_CREATION"]

    fetched = await repo.get_by_id("dept-mkt")
    assert fetched is not None
    assert fetched.name == "Marketing"

    all_depts = await repo.list_all()
    assert len(all_depts) >= 1


@pytest.mark.asyncio
async def test_cross_department_request_repository_crud(db_session):
    req_repo = SQLAlchemyDepartmentRequestRepository(db_session)
    handoff_repo = SQLAlchemyDepartmentHandoffRepository(db_session)

    req = DepartmentRequest(
        request_id="req-1",
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-p1",
        receiving_manager_id="emp-e1",
        purpose="Build feature X",
        requested_outcome="API deployed",
        priority=DepartmentPriority.HIGH,
    )

    saved_req = await req_repo.save(req)
    assert saved_req.request_id == "req-1"
    assert saved_req.status == DepartmentRequestStatus.REQUESTED

    # Accept request
    saved_req.status = DepartmentRequestStatus.ACCEPTED
    saved_req.delivery_owner_employee_id = "emp-dev-1"
    updated_req = await req_repo.save(saved_req)
    assert updated_req.status == DepartmentRequestStatus.ACCEPTED

    # Create Handoff
    handoff = DepartmentHandoff(
        handoff_id="h-1",
        request_id="req-1",
        sender_department_id="dept-eng",
        receiver_department_id="dept-prod",
        sender_employee_id="emp-dev-1",
        expected_outcome="Feature delivered",
        artifact_ids=["art-1"],
    )

    saved_h = await handoff_repo.save(handoff)
    assert saved_h.handoff_id == "h-1"

    fetched_h = await handoff_repo.get_by_request_id("req-1")
    assert fetched_h is not None
    assert fetched_h.sender_department_id == "dept-eng"
