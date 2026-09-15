"""Failure injection test suite for Phase 14 Department operating framework."""

import pytest
from unittest.mock import AsyncMock
from src.domain.department import Department
from src.domain.cross_department import DepartmentRequest, DepartmentRequestStatus, HandoffStatus
from src.application.cross_department_service import CrossDepartmentService


@pytest.mark.asyncio
async def test_request_rejection_and_escalation():
    mock_dept_repo = AsyncMock()
    mock_req_repo = AsyncMock()
    mock_handoff_repo = AsyncMock()

    mock_dept_repo.get_by_id.side_effect = lambda d_id: Department(id=d_id, name=d_id, code=d_id.upper())

    service = CrossDepartmentService(
        department_repository=mock_dept_repo,
        request_repository=mock_req_repo,
        handoff_repository=mock_handoff_repo,
    )

    req = await service.submit_request(
        requester_department_id="dept-mkt",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-mkt-1",
        purpose="Campaign page build",
        requested_outcome="Landing page live",
    )

    mock_req_repo.get_by_id.return_value = req
    rejected = await service.reject_request(
        request_id=req.request_id,
        receiving_manager_id="emp-eng-mgr",
        reason="Resource constraints in Q3",
    )

    assert rejected.status == DepartmentRequestStatus.REJECTED
    assert rejected.rejection_reason == "Resource constraints in Q3"


@pytest.mark.asyncio
async def test_handoff_verification_failure():
    mock_dept_repo = AsyncMock()
    mock_req_repo = AsyncMock()
    mock_handoff_repo = AsyncMock()

    req = AsyncMock(request_id="req-55", status=DepartmentRequestStatus.DELIVERED)
    mock_req_repo.get_by_id.return_value = req

    service = CrossDepartmentService(
        department_repository=mock_dept_repo,
        request_repository=mock_req_repo,
        handoff_repository=mock_handoff_repo,
    )

    handoff = await service.submit_handoff(
        request_id="req-55",
        sender_employee_id="emp-dev-2",
        expected_outcome="Feature X build",
    )

    mock_handoff_repo.get_by_id.return_value = handoff
    verified_failed = await service.verify_handoff(
        handoff_id=handoff.handoff_id,
        verifier_employee_id="emp-qa-lead",
        is_approved=False,
        reason="Integration test suite failed in QA environment",
    )

    assert verified_failed.is_verified is False
    assert verified_failed.status == HandoffStatus.REJECTED
    assert "Integration test suite failed" in verified_failed.rejection_reason
