"""Unit tests for Phase 14 Department Domain Entities and Events."""

import pytest
from datetime import UTC, datetime
from src.domain.department import (
    Department,
    DepartmentHealth,
    DepartmentPriority,
    DepartmentStatus,
)
from src.domain.cross_department import (
    DepartmentHandoff,
    DepartmentHealthReport,
    DepartmentMetrics,
    DepartmentRequest,
    DepartmentRequestStatus,
    DepartmentServiceContract,
    HandoffStatus,
)
from src.domain.events import (
    DepartmentCreatedEvent,
    DepartmentHandoffCreatedEvent,
    DepartmentHealthChangedEvent,
    DepartmentRequestCreatedEvent,
)


def test_department_entity_creation():
    dept = Department(
        id="dept-eng",
        name="Engineering",
        code="ENG",
        description="Software development department",
        status=DepartmentStatus.ACTIVE,
        purpose="Build and maintain software",
        capabilities=["SOFTWARE_DEVELOPMENT", "CODE_REVIEW"],
    )
    assert dept.id == "dept-eng"
    assert dept.status == DepartmentStatus.ACTIVE
    assert "SOFTWARE_DEVELOPMENT" in dept.capabilities


def test_department_request_entity():
    req = DepartmentRequest(
        request_id="req-101",
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod-mgr",
        receiving_manager_id="emp-eng-mgr",
        purpose="Build API feature",
        requested_outcome="REST endpoint",
        priority=DepartmentPriority.HIGH,
    )
    assert req.request_id == "req-101"
    assert req.status == DepartmentRequestStatus.REQUESTED
    assert req.priority == DepartmentPriority.HIGH


def test_department_handoff_entity():
    handoff = DepartmentHandoff(
        handoff_id="h-01",
        request_id="req-101",
        sender_department_id="dept-eng",
        receiver_department_id="dept-qa",
        sender_employee_id="emp-dev-1",
        expected_outcome="Feature implementation ready for QA",
        artifact_ids=["art-1"],
        evidence_ids=["ev-1"],
    )
    assert handoff.handoff_id == "h-01"
    assert handoff.status == HandoffStatus.PROPOSED
    assert handoff.is_verified is False


def test_department_health_report():
    metrics = DepartmentMetrics(
        department_id="dept-qa",
        active_tasks=5,
        blocked_tasks=2,
    )
    report = DepartmentHealthReport(
        department_id="dept-qa",
        health=DepartmentHealth.AT_RISK,
        reason="Downstream dependency congestion",
        metrics=metrics,
    )
    assert report.health == DepartmentHealth.AT_RISK
    assert report.metrics.blocked_tasks == 2


def test_department_events():
    evt1 = DepartmentCreatedEvent(department_id="d1", name="Legal", code="LEG")
    assert evt1.name == "Legal"

    evt2 = DepartmentRequestCreatedEvent(
        request_id="r1",
        requester_department_id="d1",
        receiving_department_id="d2",
        purpose="Contract review",
    )
    assert evt2.purpose == "Contract review"
