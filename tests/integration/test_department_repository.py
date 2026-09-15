"""Integration tests for Phase 14 SQLAlchemyDepartmentRepository."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.department import (
    Department,
    DepartmentHandoff,
    DepartmentHealth,
    DepartmentMetrics,
    DepartmentRequest,
    DepartmentRequestPriority,
    DepartmentRequestStatus,
    DepartmentServiceContract,
    DepartmentStatus,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository


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
        id="dept-mktg",
        name="Marketing",
        code="MKTG",
        description="Marketing and Communications",
        purpose="Drive brand awareness and lead generation",
        status=DepartmentStatus.ACTIVE,
        responsibilities=["campaigns", "content"],
        capabilities=["MARKETING_RESEARCH", "CONTENT_CREATION"],
    )

    saved = await repo.save(dept)
    assert saved.id == "dept-mktg"

    fetched = await repo.get_by_id("dept-mktg")
    assert fetched is not None
    assert fetched.name == "Marketing"
    assert "CONTENT_CREATION" in fetched.capabilities

    all_depts = await repo.list_all()
    assert len(all_depts) >= 1


@pytest.mark.asyncio
async def test_department_request_and_handoff_persistence(db_session):
    repo = SQLAlchemyDepartmentRepository(db_session)

    req = DepartmentRequest(
        request_id="req-1",
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod",
        purpose="Develop REST API",
        requested_outcome="Working REST endpoint",
        priority=DepartmentRequestPriority.HIGH,
        status=DepartmentRequestStatus.REQUESTED,
    )

    saved_req = await repo.save_request(req)
    assert saved_req.request_id == "req-1"

    fetched_req = await repo.get_request("req-1")
    assert fetched_req is not None
    assert fetched_req.priority == DepartmentRequestPriority.HIGH

    handoff = DepartmentHandoff(
        handoff_id="h-1",
        request_id="req-1",
        sender_department_id="dept-eng",
        receiving_department_id="dept-qa",
        sender_employee_id="emp-eng",
        expected_outcome="Passing test suite",
    )
    saved_h = await repo.save_handoff(handoff)
    assert saved_h.handoff_id == "h-1"

    fetched_h = await repo.get_handoff("h-1")
    assert fetched_h is not None
    assert fetched_h.status == "PENDING_VERIFICATION"


@pytest.mark.asyncio
async def test_department_metrics_persistence(db_session):
    repo = SQLAlchemyDepartmentRepository(db_session)

    metrics = DepartmentMetrics(
        department_id="dept-eng",
        active_task_count=5,
        blocked_task_count=1,
        health=DepartmentHealth.HEALTHY,
    )

    await repo.save_metrics(metrics)
    fetched_m = await repo.get_metrics("dept-eng")
    assert fetched_m is not None
    assert fetched_m.health == DepartmentHealth.HEALTHY
    assert fetched_m.active_task_count == 5
