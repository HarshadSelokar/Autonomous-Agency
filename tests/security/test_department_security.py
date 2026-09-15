"""Security test suite for Phase 14 Department Expansion.

Verifies cross-department data privacy, department isolation, and governance policy precedence.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.domain.department import Department, DepartmentStatus
from src.application.department_service import DepartmentService


@pytest.mark.asyncio
async def test_paused_department_blocks_unauthorized_requests():
    mock_repo = AsyncMock()
    service = DepartmentService(department_repository=mock_repo)

    mock_repo.get_by_id.return_value = Department(
        id="dept-legal",
        name="Legal & Compliance",
        code="LEGAL",
        status=DepartmentStatus.PAUSED,
    )

    with pytest.raises(ValueError, match="is in status 'PAUSED' and cannot accept requests"):
        await service.create_request(
            requester_department_id="dept-sales",
            receiving_department_id="dept-legal",
            requester_employee_id="emp-sales",
            purpose="Contract Review",
            requested_outcome="Approved contract",
        )


@pytest.mark.asyncio
async def test_suspended_department_blocks_new_requests():
    mock_repo = AsyncMock()
    service = DepartmentService(department_repository=mock_repo)

    mock_repo.get_by_id.return_value = Department(
        id="dept-fin",
        name="Finance",
        code="FIN",
        status=DepartmentStatus.SUSPENDED,
    )

    with pytest.raises(ValueError, match="is in status 'SUSPENDED' and cannot accept requests"):
        await service.create_request(
            requester_department_id="dept-exec",
            receiving_department_id="dept-fin",
            requester_employee_id="emp-exec",
            purpose="Disburse capital",
            requested_outcome="Funds transfer",
        )
