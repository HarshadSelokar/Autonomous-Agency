"""Office Projection Service.

Translates authoritative backend Company OS state into deterministic Pixel Office projections.
Ensures THE COMPANY OS IS REALITY and THE PIXEL OFFICE VISUALIZES REALITY.
"""

import logging
from inspect import isawaitable
from typing import Any

from src.domain.office import (
    DepartmentLayoutProjection,
    EmployeeVisualState,
    EmployeeWorkstationProjection,
    HumanAttentionItem,
    HumanAttentionType,
    OfficeActivityItem,
    OfficeAreaType,
    OfficeCompanyProjection,
)

logger = logging.getLogger(__name__)


class OfficeProjectionService:
    """Application service for projecting authoritative backend state to Pixel Office views."""

    def __init__(
        self,
        employee_repository: Any = None,
        department_repository: Any = None,
        task_repository: Any = None,
        project_repository: Any = None,
        meeting_repository: Any = None,
        governance_repository: Any = None,
        verification_repository: Any = None,
        recovery_repository: Any = None,
        agent_run_repository: Any = None,
        office_repository: Any = None,
    ) -> None:
        self.employee_repo = employee_repository
        self.department_repo = department_repository
        self.task_repo = task_repository
        self.project_repo = project_repository
        self.meeting_repo = meeting_repository
        self.governance_repo = governance_repository
        self.verification_repo = verification_repository
        self.recovery_repo = recovery_repository
        self.agent_run_repo = agent_run_repository
        self.office_repo = office_repository

    def derive_employee_visual_state(
        self,
        employee_id: str,
        employee_status: str = "ACTIVE",
        is_governance_paused: bool = False,
        is_recovering: bool = False,
        is_awaiting_approval: bool = False,
        is_verifying: bool = False,
        is_task_blocked: bool = False,
        is_in_meeting: bool = False,
        is_agent_running: bool = False,
        is_task_in_progress: bool = False,
    ) -> EmployeeVisualState:
        """Deterministically map backend states to EmployeeVisualState."""
        if employee_status.upper() in ("OFFLINE", "INACTIVE"):
            return EmployeeVisualState.OFFLINE

        if is_governance_paused:
            return EmployeeVisualState.PAUSED

        if is_recovering:
            return EmployeeVisualState.RECOVERING

        if is_awaiting_approval:
            return EmployeeVisualState.AWAITING_APPROVAL

        if is_verifying:
            return EmployeeVisualState.REVIEWING

        if is_task_blocked:
            return EmployeeVisualState.BLOCKED

        if is_in_meeting:
            return EmployeeVisualState.IN_MEETING

        if is_agent_running or is_task_in_progress:
            return EmployeeVisualState.WORKING

        return EmployeeVisualState.IDLE

    def project_workstation(
        self,
        employee_id: str,
        employee_name: str,
        employee_title: str,
        role: str,
        department_id: str | None,
        visual_state: EmployeeVisualState,
        desk_id: str | None = None,
        area_type: OfficeAreaType = OfficeAreaType.ENGINEERING,
        manager_id: str | None = None,
        current_task_id: str | None = None,
        current_task_title: str | None = None,
        current_project_id: str | None = None,
        current_project_name: str | None = None,
        current_activity_summary: str | None = None,
        active_agent_id: str | None = None,
        active_tool_name: str | None = None,
        active_model_id: str | None = None,
        is_manager: bool = False,
    ) -> EmployeeWorkstationProjection:
        """Build an employee workstation projection."""
        return EmployeeWorkstationProjection(
            employee_id=str(employee_id),
            employee_name=employee_name,
            employee_title=employee_title,
            role=role,
            department_id=str(department_id) if department_id else None,
            manager_id=str(manager_id) if manager_id else None,
            desk_id=desk_id or f"desk-{employee_id}",
            area_type=area_type,
            visual_state=visual_state,
            current_task_id=str(current_task_id) if current_task_id else None,
            current_task_title=current_task_title,
            current_project_id=str(current_project_id) if current_project_id else None,
            current_project_name=current_project_name,
            current_activity_summary=current_activity_summary or f"Status: {visual_state.value}",
            active_agent_id=str(active_agent_id) if active_agent_id else None,
            active_tool_name=active_tool_name,
            active_model_id=active_model_id,
            is_manager=is_manager,
        )

    async def build_company_overview(
        self,
        organization_id: str | None = None,
        viewer_id: str | None = None,
    ) -> OfficeCompanyProjection:
        """Assemble the authoritative company overview for the Pixel Office."""
        employees = []
        if self.employee_repo and hasattr(self.employee_repo, "list_all"):
            res = self.employee_repo.list_all()
            employees = await res if isawaitable(res) else res

        workstations: list[EmployeeWorkstationProjection] = []
        dept_map: dict[str, list[EmployeeWorkstationProjection]] = {}

        is_gov_paused = False
        if self.governance_repo and hasattr(self.governance_repo, "is_emergency_stopped"):
            res = self.governance_repo.is_emergency_stopped()
            is_gov_paused = await res if isawaitable(res) else res

        working_count = 0
        meeting_count = 0
        blocked_count = 0
        recovering_count = 0

        for emp in employees:
            emp_id = str(getattr(emp, "id", None) or getattr(emp, "employee_id", ""))
            emp_name = getattr(emp, "name", "Employee")
            dept_id = str(getattr(emp, "department_id", "")) or None
            dept_name = getattr(emp, "department_name", "General") or "General"
            title = getattr(emp, "title", "Staff")
            role = getattr(emp, "role", "DEVELOPER")
            emp_status = getattr(emp, "status", "ACTIVE")

            is_recovering = False
            if self.recovery_repo and hasattr(self.recovery_repo, "has_active_recovery"):
                res = self.recovery_repo.has_active_recovery(emp_id)
                is_recovering = await res if isawaitable(res) else res
                if is_recovering:
                    recovering_count += 1

            is_awaiting_appr = False
            if self.governance_repo and hasattr(self.governance_repo, "has_pending_approval"):
                res = self.governance_repo.has_pending_approval(emp_id)
                is_awaiting_appr = await res if isawaitable(res) else res

            is_verifying = False
            if self.verification_repo and hasattr(self.verification_repo, "is_verifying"):
                res = self.verification_repo.is_verifying(emp_id)
                is_verifying = await res if isawaitable(res) else res

            is_blocked = False
            if is_blocked:
                blocked_count += 1

            is_in_meeting = False
            if self.meeting_repo and hasattr(self.meeting_repo, "is_employee_in_meeting"):
                res = self.meeting_repo.is_employee_in_meeting(emp_id)
                is_in_meeting = await res if isawaitable(res) else res
                if is_in_meeting:
                    meeting_count += 1

            is_agent_running = False
            if self.agent_run_repo and hasattr(self.agent_run_repo, "has_active_run"):
                res = self.agent_run_repo.has_active_run(emp_id)
                is_agent_running = await res if isawaitable(res) else res
                if is_agent_running:
                    working_count += 1

            visual_state = self.derive_employee_visual_state(
                employee_id=emp_id,
                employee_status=emp_status,
                is_governance_paused=is_gov_paused,
                is_recovering=is_recovering,
                is_awaiting_approval=is_awaiting_appr,
                is_verifying=is_verifying,
                is_task_blocked=is_blocked,
                is_in_meeting=is_in_meeting,
                is_agent_running=is_agent_running,
            )

            # Map department / title to OfficeAreaType
            t_upper = title.upper()
            d_upper = dept_name.upper()
            if "EXEC" in t_upper or "MANAGER" in t_upper or "EXEC" in d_upper:
                area_type = OfficeAreaType.EXECUTIVE
            elif "PROD" in d_upper:
                area_type = OfficeAreaType.PRODUCT
            elif "QA" in d_upper or "TEST" in d_upper:
                area_type = OfficeAreaType.QA
            elif "DEVOPS" in d_upper or "INFRA" in d_upper:
                area_type = OfficeAreaType.DEVOPS
            elif "MKT" in d_upper or "SALES" in d_upper:
                area_type = OfficeAreaType.COLLABORATION
            else:
                area_type = OfficeAreaType.ENGINEERING

            ws_proj = self.project_workstation(
                employee_id=emp_id,
                employee_name=emp_name,
                employee_title=title,
                role=role,
                department_id=dept_id,
                visual_state=visual_state,
                area_type=area_type,
            )
            workstations.append(ws_proj)

            if dept_name not in dept_map:
                dept_map[dept_name] = []
            dept_map[dept_name].append(ws_proj)

        departments: list[DepartmentLayoutProjection] = []
        for name, ws_list in dept_map.items():
            d_upper = name.upper()
            if "EXEC" in d_upper:
                area_type = OfficeAreaType.EXECUTIVE
            elif "PROD" in d_upper:
                area_type = OfficeAreaType.PRODUCT
            elif "QA" in d_upper:
                area_type = OfficeAreaType.QA
            elif "DEVOPS" in d_upper:
                area_type = OfficeAreaType.DEVOPS
            else:
                area_type = OfficeAreaType.ENGINEERING

            departments.append(
                DepartmentLayoutProjection(
                    department_id=ws_list[0].department_id if ws_list and ws_list[0].department_id else "dept-1",
                    name=name,
                    area_type=area_type,
                    active_employee_ids=[w.employee_id for w in ws_list],
                )
            )

        attention_items: list[HumanAttentionItem] = []
        activity_feed: list[OfficeActivityItem] = []
        if self.office_repo:
            if hasattr(self.office_repo, "list_human_attention_items"):
                res = self.office_repo.list_human_attention_items()
                attention_items = await res if isawaitable(res) else res
            if hasattr(self.office_repo, "list_recent_activity"):
                res = self.office_repo.list_recent_activity()
                activity_feed = await res if isawaitable(res) else res

        return OfficeCompanyProjection(
            company_name="Autonomous AI Organization",
            is_emergency_stopped=is_gov_paused,
            active_employees_count=len(employees),
            working_employees_count=working_count,
            in_meeting_employees_count=meeting_count,
            blocked_tasks_count=blocked_count,
            pending_approvals_count=len([item for item in attention_items if item.attention_type == HumanAttentionType.APPROVAL_REQUIRED]),
            active_projects_count=1,
            failed_verifications_count=len([item for item in attention_items if item.attention_type == HumanAttentionType.FAILED_VERIFICATION]),
            active_recoveries_count=recovering_count,
            attention_items=attention_items,
            recent_activities=activity_feed,
            departments=departments,
        )
