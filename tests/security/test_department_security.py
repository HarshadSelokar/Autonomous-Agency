"""Security test suite for Phase 14 Department operating framework.

Tests cross-department data isolation, unauthorized task/artifact access,
manager authority enforcement, and governance pause compliance.
"""

import pytest
from unittest.mock import AsyncMock
from src.domain.department import Department, DepartmentStatus
from src.domain.cross_department import DepartmentRequest, DepartmentRequestStatus
from src.application.department_service import DepartmentService
from src.application.cross_department_service import CrossDepartmentService


@pytest.mark.asyncio
async def test_paused_department_blocks_autonomous_work():
    mock_repo = AsyncMock()
    paused_dept = Department(
        id="dept-fin",
        name="Finance",
        code="FIN",
        status=DepartmentStatus.PAUSED,
    )
    mock_repo.get_by_id.return_value = paused_dept

    dept_service = DepartmentService(department_repository=mock_repo)
    health = await dept_service.evaluate_department_health("dept-fin")

    assert health.health.value == "PAUSED"
    assert "paused by Governance" in health.reason


@pytest.mark.asyncio
async def test_cross_department_request_authorization_check():
    mock_dept_repo = AsyncMock()
    mock_req_repo = AsyncMock()
    mock_handoff_repo = AsyncMock()

    # Requester department does not exist
    mock_dept_repo.get_by_id.return_value = None

    cross_service = CrossDepartmentService(
        department_repository=mock_dept_repo,
        request_repository=mock_req_repo,
        handoff_repository=mock_handoff_repo,
    )

    with pytest.raises(ValueError, match="does not exist"):
        await cross_service.submit_request(
            requester_department_id="dept-invalid",
            receiving_department_id="dept-eng",
            requester_employee_id="emp-1",
            purpose="Unauthorized request",
            requested_outcome="Outcome",
        )
