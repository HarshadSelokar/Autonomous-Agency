"""Failure injection test suite for Phase 14 Department Expansion.

Tests deliverable handoff verification failures, recovery engine triggers,
and department bottleneck detection.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.domain.department import (
    DepartmentHandoff,
    DepartmentHealth,
    DepartmentMetrics,
    DepartmentRequest,
    DepartmentRequestStatus,
)
from src.application.department_service import DepartmentService


@pytest.mark.asyncio
async def test_handoff_verification_failure_triggers_recovery():
    mock_repo = AsyncMock()
    mock_recovery = AsyncMock()

    service = DepartmentService(
        department_repository=mock_repo,
        recovery_engine=mock_recovery,
    )

    req = DepartmentRequest(
        request_id="req-fail-1",
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod",
        purpose="Develop API",
        requested_outcome="Working API",
        status=DepartmentRequestStatus.DELIVERED,
    )
    handoff = DepartmentHandoff(
        handoff_id="h-fail-1",
        request_id="req-fail-1",
        sender_department_id="dept-eng",
        receiving_department_id="dept-prod",
        sender_employee_id="emp-eng",
        expected_outcome="Passing integration test suite",
    )

    mock_repo.get_handoff.return_value = handoff
    mock_repo.get_request.return_value = req

    updated_req = await service.verify_handoff(
        handoff_id="h-fail-1",
        verifier_employee_id="emp-prod",
        success=False,
        reason="Tests failed on endpoint 500 error",
    )

    assert updated_req.status == DepartmentRequestStatus.BLOCKED
    assert handoff.status == "VERIFICATION_FAILED"


@pytest.mark.asyncio
async def test_department_bottleneck_health_degradation():
    mock_repo = AsyncMock()
    service = DepartmentService(department_repository=mock_repo)

    # 6 blocked incoming requests
    blocked_requests = [
        DepartmentRequest(
            request_id=f"req-{i}",
            requester_department_id="dept-prod",
            receiving_department_id="dept-qa",
            requester_employee_id="emp-prod",
            purpose="Testing",
            requested_outcome="Outcome",
            status=DepartmentRequestStatus.BLOCKED,
        )
        for i in range(6)
    ]

    mock_repo.list_requests.return_value = blocked_requests
    mock_repo.save_metrics.side_effect = lambda x: x

    metrics = await service.calculate_department_health("dept-qa")
    assert metrics.health == DepartmentHealth.DEGRADED
    assert metrics.blocked_task_count == 6
