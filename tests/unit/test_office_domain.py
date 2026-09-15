"""
Unit tests for Phase 13 Pixel Office Domain Entities & Projection Enums.
"""

from datetime import datetime, timezone
import pytest

from src.domain.office import (
    DepartmentLayoutProjection,
    EmployeeVisualState,
    EmployeeWorkstationProjection,
    HumanAttentionItem,
    HumanAttentionType,
    OfficeActivityItem,
    OfficeAreaType,
    OfficeCompanyProjection,
    OfficeMeetingRoomProjection,
    OfficeProjectAreaProjection,
)


def test_employee_workstation_projection_creation():
    projection = EmployeeWorkstationProjection(
        employee_id="emp-101",
        employee_name="Alice Developer",
        employee_title="Senior Engineer",
        role="DEVELOPER",
        department_id="dept-eng",
        manager_id="emp-mgr-1",
        desk_id="desk-eng-01",
        area_type=OfficeAreaType.ENGINEERING,
        visual_state=EmployeeVisualState.WORKING,
        current_task_id="task-1",
        current_activity_summary="Implementing authentication feature",
        is_manager=False,
    )

    assert projection.employee_id == "emp-101"
    assert projection.visual_state == EmployeeVisualState.WORKING
    assert projection.area_type == OfficeAreaType.ENGINEERING
    assert projection.desk_id == "desk-eng-01"


def test_human_attention_item_creation():
    item = HumanAttentionItem(
        item_id="att-1",
        attention_type=HumanAttentionType.APPROVAL_REQUIRED,
        title="Production Deploy Approval",
        description="Release v1.0 requires manager signature",
        entity_id="appr-99",
        entity_type="APPROVAL",
        severity="HIGH",
    )

    assert item.attention_type == HumanAttentionType.APPROVAL_REQUIRED
    assert item.entity_id == "appr-99"
    assert item.severity == "HIGH"


def test_office_company_projection_aggregates():
    company = OfficeCompanyProjection(
        company_name="Autonomous Software Inc",
        is_emergency_stopped=False,
        active_employees_count=12,
        working_employees_count=8,
        in_meeting_employees_count=2,
        blocked_tasks_count=1,
        pending_approvals_count=2,
        active_projects_count=3,
        failed_verifications_count=1,
        active_recoveries_count=1,
    )

    assert company.company_name == "Autonomous Software Inc"
    assert company.working_employees_count == 8
    assert not company.is_emergency_stopped
