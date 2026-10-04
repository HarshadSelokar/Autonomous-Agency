"""
Unit and isolation tests for TenantWorkforceService (Phase 34).
"""

import pytest
from unittest.mock import AsyncMock
from src.domain.employee import Employee, EmployeeStatus, EmployeeCapability
from src.domain.exceptions import SecurityBoundaryViolationError, QuotaExceededError
from src.application.tenant_workforce_service import TenantWorkforceService


@pytest.mark.asyncio
async def test_tenant_workforce_filtering():
    emp1 = Employee(
        id="emp-1",
        employee_code="EMP-001",
        name="Alice",
        title="Senior Engineer",
        role="ENGINEER",
        agent_id="agt-1",
        capabilities=[EmployeeCapability(name="code")],
        status=EmployeeStatus.ACTIVE,
    )
    emp1.tenant_id = "tenant-A"
    emp1.workload = 0.2

    emp2 = Employee(
        id="emp-2",
        employee_code="EMP-002",
        name="Bob",
        title="Senior Engineer",
        role="ENGINEER",
        agent_id="agt-2",
        capabilities=[EmployeeCapability(name="code")],
        status=EmployeeStatus.ACTIVE,
    )
    emp2.tenant_id = "tenant-B"
    emp2.workload = 0.1

    repo_mock = AsyncMock()
    repo_mock.list_all.return_value = [emp1, emp2]

    service = TenantWorkforceService(employee_repo=repo_mock)

    res_a = await service.get_available_employees_for_tenant("tenant-A", required_capability="code")
    assert len(res_a) == 1
    assert res_a[0].id == "emp-1"


@pytest.mark.asyncio
async def test_cross_tenant_allocation_prevention():
    emp = Employee(
        id="emp-1",
        employee_code="EMP-001",
        name="Alice",
        title="Senior Engineer",
        role="ENGINEER",
        agent_id="agt-1",
        capabilities=[EmployeeCapability(name="code")],
        status=EmployeeStatus.ACTIVE,
    )
    emp.tenant_id = "tenant-A"

    repo_mock = AsyncMock()
    repo_mock.get_by_id.return_value = emp

    service = TenantWorkforceService(employee_repo=repo_mock)

    # Attempting to allocate Tenant A's employee to Tenant B should raise SecurityBoundaryViolationError
    with pytest.raises(SecurityBoundaryViolationError):
        await service.allocate_employee_to_task(
            tenant_id="tenant-B",
            employee_id="emp-1",
            task_id="task-100",
        )
