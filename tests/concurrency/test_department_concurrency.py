"""Concurrency test suite for Phase 14 Department framework."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.application.cross_department_service import CrossDepartmentService
from src.domain.cross_department import DepartmentPriority
from src.domain.department import Department


@pytest.mark.asyncio
async def test_simultaneous_cross_department_requests():
    mock_dept_repo = AsyncMock()
    mock_req_repo = AsyncMock()
    mock_handoff_repo = AsyncMock()

    mock_dept_repo.get_by_id.side_effect = lambda d_id: Department(id=d_id, name=d_id, code=d_id.upper())
    mock_req_repo.save.side_effect = lambda req: req

    service = CrossDepartmentService(
        department_repository=mock_dept_repo,
        request_repository=mock_req_repo,
        handoff_repository=mock_handoff_repo,
    )

    tasks = [
        service.submit_request(
            requester_department_id="dept-sales",
            receiving_department_id="dept-fin",
            requester_employee_id="emp-sales-rep",
            purpose=f"Pricing approval #{i}",
            requested_outcome="Custom quote approved",
            priority=DepartmentPriority.HIGH,
        )
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)
    assert len(results) == 10
    assert len({r.request_id for r in results}) == 10
