"""
Unit tests for Workforce domain entities.
"""

import pytest

from src.domain.workforce import (
    CapabilityGap,
    CapacitySnapshot,
    EmployeeTemplate,
    GapSeverity,
    StaffingPlanStatus,
    WorkforceChangeRequest,
    WorkforceChangeRequestStatus,
    WorkforceChangeRequestType,
    WorkforceDemand,
    WorkforcePlan,
)


def test_workforce_demand_creation():
    demand = WorkforceDemand(
        source_type="PROJECT",
        source_id="proj-1",
        capability="BACKEND_DEVELOPMENT",
        required_count=3,
        priority=4,
    )
    assert demand.capability == "BACKEND_DEVELOPMENT"
    assert demand.required_count == 3
    assert demand.priority == 4


def test_workforce_demand_invalid_count():
    with pytest.raises(ValueError):
        WorkforceDemand(
            source_type="PROJECT",
            source_id="proj-1",
            capability="BACKEND_DEVELOPMENT",
            required_count=0,
        )


def test_capacity_snapshot_calculation():
    snap = CapacitySnapshot(
        employee_id="emp-1",
        capability="BACKEND_DEVELOPMENT",
        max_capacity=1.0,
        allocated_capacity=0.6,
    )
    avail = snap.calculate_available()
    assert avail == pytest.approx(0.4)
    assert snap.available_capacity == pytest.approx(0.4)


def test_capability_gap_creation():
    gap = CapabilityGap(
        capability="SECURITY",
        required_count=5,
        available_count=2,
        gap_count=3,
        severity=GapSeverity.HIGH,
        affected_project_ids=["proj-101"],
    )
    assert gap.gap_count == 3
    assert gap.severity == GapSeverity.HIGH


def test_staffing_plan_lifecycle():
    plan = WorkforcePlan(
        planning_horizon="Q3",
        objectives=["obj-1"],
        status=StaffingPlanStatus.DRAFT,
    )
    assert plan.status == StaffingPlanStatus.DRAFT


def test_workforce_change_request():
    req = WorkforceChangeRequest(
        request_type=WorkforceChangeRequestType.FORM_TEAM,
        target_id="team-alpha",
        requested_by_id="mgr-1",
        justification="Project launch requirement",
    )
    assert req.status == WorkforceChangeRequestStatus.PENDING
    assert req.request_type == WorkforceChangeRequestType.FORM_TEAM


def test_employee_template():
    tpl = EmployeeTemplate(
        title="Senior Backend Engineer",
        role="ENGINEER",
        capabilities=["BACKEND_DEVELOPMENT", "API_DESIGN"],
        skills=["Python", "FastAPI"],
    )
    assert "BACKEND_DEVELOPMENT" in tpl.capabilities
    assert "Python" in tpl.skills
