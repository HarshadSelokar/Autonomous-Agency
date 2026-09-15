"""Concurrency test suite for Phase 14 Department Expansion.

Tests concurrent cross-department request creation and acceptance.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

from src.domain.department import Department, DepartmentRequestPriority, DepartmentStatus
from src.application.department_service import DepartmentService


@pytest.mark.asyncio
async def test_concurrent_cross_department_requests():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = Department(
        id="dept-eng",
        name="Engineering",
        code="ENG",
        status=DepartmentStatus.ACTIVE,
    )
    mock_repo.save_request.side_effect = lambda x: x

    service = DepartmentService(department_repository=mock_repo)

    tasks = [
        service.create_request(
            requester_department_id=f"dept-req-{i}",
            receiving_department_id="dept-eng",
            requester_employee_id=f"emp-{i}",
            purpose=f"Feature {i}",
            requested_outcome=f"Deliverable {i}",
            priority=DepartmentRequestPriority.MEDIUM,
        )
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)
    assert len(results) == 10
    for r in results:
        assert r.receiving_department_id == "dept-eng"
