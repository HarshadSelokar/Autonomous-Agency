"""
Integration tests for Phase 9 AI Software Company REST API endpoints.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.domain.employee import Employee, EmployeeCapability, EmployeeStatus
from src.domain.objective import Objective
from src.infrastructure.database import Base, get_db
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Create prerequisite Objective & Manager Employee
        obj_repo = SQLAlchemyObjectiveRepository(session)
        emp_repo = SQLAlchemyEmployeeRepository(session)

        await obj_repo.save(
            Objective(id="obj-api-1", title="Build Customer API", description="Customer API Spec", requester="CEO")
        )
        await emp_repo.save(
            Employee(
                id="emp-mgr-alice",
                employee_code="EMP-MGR-1",
                name="Alice Manager",
                role="Engineering Manager",
                title="Director of Engineering",
                agent_id="agent-mgr",
                capabilities=[EmployeeCapability(name="planning"), EmployeeCapability(name="SOFTWARE_ARCHITECTURE")],
                status=EmployeeStatus.ACTIVE,
            )
        )
        await emp_repo.save(
            Employee(
                id="emp-dev-bob",
                employee_code="EMP-DEV-1",
                name="Bob Developer",
                role="Backend Developer",
                title="Senior Developer",
                agent_id="agent-dev",
                capabilities=[EmployeeCapability(name="BACKEND_DEVELOPMENT")],
                status=EmployeeStatus.ACTIVE,
            )
        )
        await emp_repo.save(
            Employee(
                id="emp-qa-charlie",
                employee_code="EMP-QA-1",
                name="Charlie QA",
                role="QA Engineer",
                title="QA Engineer",
                agent_id="agent-qa",
                capabilities=[EmployeeCapability(name="QA_ENGINEERING")],
                status=EmployeeStatus.ACTIVE,
            )
        )
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_software_project_api_lifecycle(api_client: AsyncClient):
    # 1. Create Software Project
    res = await api_client.post(
        "/software-projects",
        json={
            "objective_id": "obj-api-1",
            "name": "Customer API Microservice",
            "description": "API for customer records",
            "repository_path": "/repos/customer-api",
            "workspace_id": "ws-api-1",
        },
    )
    assert res.status_code == 201
    proj_data = res.json()
    proj_id = proj_data["project_id"]
    assert proj_data["name"] == "Customer API Microservice"

    # 2. Add Requirements
    res_req = await api_client.post(
        f"/software-projects/{proj_id}/requirements",
        json={
            "requirements": [
                {
                    "title": "POST /customers Endpoint",
                    "description": "Create customer record",
                    "acceptance_criteria": ["201 Created"],
                    "priority": "HIGH",
                }
            ]
        },
    )
    assert res_req.status_code == 200
    reqs = res_req.json()
    assert len(reqs) == 1

    # 3. Create Engineering Plan
    res_plan = await api_client.post(
        f"/software-projects/{proj_id}/plan",
        json={
            "manager_employee_id": "emp-mgr-alice",
            "architecture_overview": "FastAPI + SQLite async architecture",
            "tech_stack": ["Python", "FastAPI"],
        },
    )
    assert res_plan.status_code == 200
    plan_data = res_plan.json()
    assert len(plan_data["task_ids"]) == 4

    # 4. Get Project Status
    res_status = await api_client.get(f"/software-projects/{proj_id}/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["requirements_count"] == 1
    assert status_data["tasks_count"] == 4


@pytest.mark.asyncio
async def test_code_review_and_delivery_api(api_client: AsyncClient):
    # Create Project first
    res = await api_client.post(
        "/software-projects",
        json={
            "objective_id": "obj-api-1",
            "name": "API Service",
            "repository_path": "/repos/api",
        },
    )
    proj_id = res.json()["project_id"]

    # Submit Code Change
    res_change = await api_client.post(
        "/code-changes",
        json={
            "project_id": proj_id,
            "task_id": "task-api-1",
            "author_employee_id": "emp-dev-bob",
            "files_changed": ["main.py"],
            "diff_summary": "+ def app(): pass",
            "branch_name": "feature/api",
        },
    )
    assert res_change.status_code == 201
    change_id = res_change.json()["change_id"]

    # Self-approval block check via API
    res_self = await api_client.post(
        f"/code-changes/{change_id}/review-request",
        json={"change_id": change_id, "reviewer_employee_id": "emp-dev-bob"},
    )
    assert res_self.status_code == 403

    # Authorized Review Request
    res_rev_req = await api_client.post(
        f"/code-changes/{change_id}/review-request",
        json={"change_id": change_id, "reviewer_employee_id": "emp-qa-charlie"},
    )
    assert res_rev_req.status_code == 200
    review_id = res_rev_req.json()["review_id"]

    # Approve Review
    res_findings = await api_client.post(
        f"/code-reviews/{review_id}/findings",
        json={"status": "APPROVED", "findings": ["Code looks good"]},
    )
    assert res_findings.status_code == 200

    # Record Passing Test Run
    res_test = await api_client.post(
        "/test-runs",
        json={
            "project_id": proj_id,
            "task_id": "task-api-1",
            "worker_employee_id": "emp-qa-charlie",
            "command": "pytest",
            "exit_code": 0,
            "total_tests": 3,
            "passed_count": 3,
            "failed_count": 0,
        },
    )
    assert res_test.status_code == 201

    # Request Delivery
    res_del_req = await api_client.post(
        f"/software-projects/{proj_id}/delivery-request",
        json={"requested_by_employee_id": "emp-dev-bob", "version": "1.0.0"},
    )
    assert res_del_req.status_code == 201
    del_id = res_del_req.json()["delivery_id"]

    # Approve Delivery
    res_del_appr = await api_client.post(
        f"/software-deliveries/{del_id}/approve",
        json={"approved_by_employee_id": "emp-mgr-alice"},
    )
    assert res_del_appr.status_code == 200
    assert res_del_appr.json()["status"] == "DELIVERED"
