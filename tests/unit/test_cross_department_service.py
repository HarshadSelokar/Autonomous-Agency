"""Unit tests for CrossDepartmentService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.domain.department import Department
from src.domain.cross_department import DepartmentPriority, DepartmentRequestStatus, HandoffStatus
from src.application.cross_department_service import CrossDepartmentService


@pytest.mark.asyncio
async def test_submit_and_accept_request():
    mock_dept_repo = AsyncMock()
    mock_req_repo = AsyncMock()
    mock_handoff_repo = AsyncMock()

    mock_dept_repo.get_by_id.side_effect = lambda dept_id: Department(
        id=dept_id, name=dept_id, code=dept_id.upper(), manager_employee_id="mgr-1"
    )
    mock_req_repo.save.side_effect = lambda req: req

    service = CrossDepartmentService(
        department_repository=mock_dept_repo,
        request_repository=mock_req_repo,
        handoff_repository=mock_handoff_repo,
    )

    req = await service.submit_request(
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod",
        purpose="Build feature Y",
        requested_outcome="API ready",
        priority=DepartmentPriority.HIGH,
    )

    assert req.requester_department_id == "dept-prod"
    assert req.receiving_department_id == "dept-eng"
    assert req.status == DepartmentRequestStatus.REQUESTED

    # Accept request
    mock_req_repo.get_by_id.return_value = req
    accepted = await service.accept_request(
        request_id=req.request_id,
        receiving_manager_id="mgr-1",
        delivery_owner_employee_id="emp-dev-1",
    )

    assert accepted.status == DepartmentRequestStatus.ACCEPTED
    assert accepted.delivery_owner_employee_id == "emp-dev-1"


@pytest.mark.asyncio
async def test_submit_and_verify_handoff():
    mock_dept_repo = AsyncMock()
    mock_req_repo = AsyncMock()
    mock_handoff_repo = AsyncMock()

    req = AsyncMock(
        request_id="req-10",
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        status=DepartmentRequestStatus.ACCEPTED,
    )
    mock_req_repo.get_by_id.return_value = req
    mock_handoff_repo.save.side_effect = lambda h: h

    service = CrossDepartmentService(
        department_repository=mock_dept_repo,
        request_repository=mock_req_repo,
        handoff_repository=mock_handoff_repo,
    )

    handoff = await service.submit_handoff(
        request_id="req-10",
        sender_employee_id="emp-dev-1",
        expected_outcome="Feature Y delivered",
        artifact_ids=["art-10"],
    )

    assert handoff.request_id == "req-10"
    assert handoff.status == HandoffStatus.PROPOSED

    mock_handoff_repo.get_by_id.return_value = handoff
    verified = await service.verify_handoff(
        handoff_id=handoff.handoff_id,
        verifier_employee_id="emp-prod",
        is_approved=True,
    )

    assert verified.is_verified is True
    assert verified.status == HandoffStatus.VERIFIED
