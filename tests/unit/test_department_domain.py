"""Unit tests for Phase 14 Department domain entities, enums, and value objects."""

from datetime import UTC, datetime
from uuid import uuid4

from src.domain.department import (
    Department,
    DepartmentCapability,
    DepartmentHandoff,
    DepartmentHealth,
    DepartmentMetrics,
    DepartmentRequest,
    DepartmentRequestPriority,
    DepartmentRequestStatus,
    DepartmentServiceContract,
    DepartmentStatus,
)
from src.domain.events import (
    DepartmentCreatedEvent,
    DepartmentHandoffCreatedEvent,
    DepartmentRequestCreatedEvent,
)


def test_department_entity_creation():
    dept = Department(
        id="dept-eng",
        name="Engineering",
        code="ENG",
        purpose="Build and maintain software systems",
        status=DepartmentStatus.ACTIVE,
        responsibilities=["software development", "architecture", "testing"],
        capabilities=[DepartmentCapability.SOFTWARE_DEVELOPMENT.value, DepartmentCapability.ARCHITECTURE.value],
    )
    assert dept.id == "dept-eng"
    assert dept.code == "ENG"
    assert dept.status == DepartmentStatus.ACTIVE
    assert len(dept.capabilities) == 2


def test_department_request_lifecycle_states():
    req = DepartmentRequest(
        request_id="req-101",
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod-mgr",
        purpose="Implement Customer Search API",
        requested_outcome="Production-ready REST API endpoint",
        priority=DepartmentRequestPriority.HIGH,
        status=DepartmentRequestStatus.REQUESTED,
    )
    assert req.request_id == "req-101"
    assert req.priority == DepartmentRequestPriority.HIGH
    assert req.status == DepartmentRequestStatus.REQUESTED


def test_department_handoff_and_contract():
    contract = DepartmentServiceContract(
        contract_id="contract-1",
        provider_department_id="dept-eng",
        consumer_department_id="dept-qa",
        service_type="DEPLOYED_TEST_ENV",
        acceptance_criteria=["API endpoints testable", "Swagger docs provided"],
    )
    assert contract.contract_id == "contract-1"
    assert contract.is_active is True

    handoff = DepartmentHandoff(
        handoff_id="handoff-1",
        request_id="req-101",
        sender_department_id="dept-eng",
        receiving_department_id="dept-qa",
        sender_employee_id="emp-dev",
        expected_outcome="Passing integration test suite",
    )
    assert handoff.handoff_id == "handoff-1"
    assert handoff.status == "PENDING_VERIFICATION"


def test_department_metrics():
    metrics = DepartmentMetrics(
        department_id="dept-eng",
        active_task_count=10,
        blocked_task_count=2,
        health=DepartmentHealth.HEALTHY,
    )
    assert metrics.department_id == "dept-eng"
    assert metrics.health == DepartmentHealth.HEALTHY


def test_department_events():
    event = DepartmentCreatedEvent(
        department_id="dept-mktg",
        name="Marketing",
        code="MKTG",
        status="PLANNED",
    )
    assert event.department_id == "dept-mktg"
    assert event.status == "PLANNED"
