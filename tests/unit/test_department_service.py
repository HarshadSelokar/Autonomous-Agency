"""Unit tests for DepartmentService and DepartmentConfigLoader."""

import pytest
from unittest.mock import AsyncMock

from src.domain.department import (
    Department,
    DepartmentHandoff,
    DepartmentHealth,
    DepartmentRequest,
    DepartmentRequestPriority,
    DepartmentRequestStatus,
    DepartmentStatus,
)
from src.application.department_config_loader import DepartmentConfigLoader
from src.application.department_service import DepartmentService


def test_department_config_loader():
    depts = DepartmentConfigLoader.load_default_departments()
    assert len(depts) == 13
    dept_ids = [d.id for d in depts]
    assert "dept-eng" in dept_ids
    assert "dept-prod" in dept_ids
    assert "dept-qa" in dept_ids
    assert "dept-mktg" in dept_ids
    assert "dept-sales" in dept_ids
    assert "dept-fin" in dept_ids
    assert "dept-legal" in dept_ids


@pytest.mark.asyncio
async def test_department_service_register_and_status():
    mock_repo = AsyncMock()
    mock_repo.save.side_effect = lambda x: x
    service = DepartmentService(department_repository=mock_repo)

    dept = await service.register_department(
        id="dept-test",
        name="Test Dept",
        code="TEST",
        purpose="Testing",
    )
    assert dept.id == "dept-test"
    mock_repo.save.assert_called_once()

    mock_repo.get_by_id.return_value = dept
    updated = await service.update_department_status("dept-test", DepartmentStatus.PAUSED)
    assert updated.status == DepartmentStatus.PAUSED


@pytest.mark.asyncio
async def test_cross_department_request_lifecycle():
    mock_repo = AsyncMock()
    mock_repo.save_request.side_effect = lambda x: x
    mock_repo.save_handoff.side_effect = lambda x: x
    service = DepartmentService(department_repository=mock_repo)

    mock_repo.get_by_id.return_value = Department(
        id="dept-eng",
        name="Engineering",
        code="ENG",
        status=DepartmentStatus.ACTIVE,
    )

    req = await service.create_request(
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod",
        purpose="Develop REST API",
        requested_outcome="Swagger spec and code",
        priority=DepartmentRequestPriority.HIGH,
    )

    assert req.priority == DepartmentRequestPriority.HIGH
    assert req.status == DepartmentRequestStatus.REQUESTED

    # Accept request
    mock_repo.get_request.return_value = req
    accepted = await service.accept_request(
        request_id=req.request_id,
        receiving_manager_id="emp-eng-mgr",
        delivery_owner_employee_id="emp-dev",
    )
    assert accepted.status == DepartmentRequestStatus.ACCEPTED

    # Deliver request
    handoff = await service.deliver_request(
        request_id=req.request_id,
        delivery_employee_id="emp-dev",
        expected_outcome="Passing CI build",
    )
    assert handoff.request_id == req.request_id
    assert handoff.status == "PENDING_VERIFICATION"

    # Verify handoff
    mock_repo.get_handoff.return_value = handoff
    verified_req = await service.verify_handoff(
        handoff_id=handoff.handoff_id,
        verifier_employee_id="emp-prod",
        success=True,
    )
    assert verified_req.status == DepartmentRequestStatus.VERIFIED


@pytest.mark.asyncio
async def test_create_request_to_paused_department_fails():
    mock_repo = AsyncMock()
    service = DepartmentService(department_repository=mock_repo)

    mock_repo.get_by_id.return_value = Department(
        id="dept-eng",
        name="Engineering",
        code="ENG",
        status=DepartmentStatus.PAUSED,
    )

    with pytest.raises(ValueError, match="is in status 'PAUSED' and cannot accept requests"):
        await service.create_request(
            requester_department_id="dept-prod",
            receiving_department_id="dept-eng",
            requester_employee_id="emp-prod",
            purpose="Develop API",
            requested_outcome="API",
        )
