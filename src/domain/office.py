"""
Pixel Office Projection Domain Entities, Enums, and Value Objects for Phase 13.
Pure read/projection models representing real Company OS backend state visually.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class EmployeeVisualState(str, Enum):
    IDLE = "IDLE"
    WORKING = "WORKING"
    THINKING = "THINKING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    IN_MEETING = "IN_MEETING"
    REVIEWING = "REVIEWING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    OFFLINE = "OFFLINE"


class OfficeAreaType(str, Enum):
    EXECUTIVE = "EXECUTIVE"
    ENGINEERING = "ENGINEERING"
    PRODUCT = "PRODUCT"
    QA = "QA"
    DEVOPS = "DEVOPS"
    MEETING_ROOM = "MEETING_ROOM"
    COLLABORATION = "COLLABORATION"
    BREAK_ROOM = "BREAK_ROOM"
    PROJECT_ROOM = "PROJECT_ROOM"


class HumanAttentionType(str, Enum):
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    ESCALATION = "ESCALATION"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"
    UNRESOLVED_BLOCKER = "UNRESOLVED_BLOCKER"
    GOVERNANCE_VIOLATION = "GOVERNANCE_VIOLATION"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


@dataclass
class EmployeeWorkstationProjection:
    """Read model projection for an employee's visual office desk/workstation."""
    employee_id: str
    employee_name: str
    employee_title: str
    role: str
    department_id: str | None
    manager_id: str | None
    desk_id: str
    area_type: OfficeAreaType
    visual_state: EmployeeVisualState
    current_task_id: str | None = None
    current_task_title: str | None = None
    current_project_id: str | None = None
    current_project_name: str | None = None
    current_activity_summary: str = "Idle"
    active_agent_id: str | None = None
    active_tool_name: str | None = None
    active_model_id: str | None = None
    is_manager: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentLayoutProjection:
    """Read model projection for a department's office area layout."""
    department_id: str
    name: str
    area_type: OfficeAreaType
    head_employee_id: str | None = None
    total_desks: int = 10
    occupied_desks: int = 0
    active_employee_ids: list[str] = field(default_factory=list)


@dataclass
class OfficeMeetingRoomProjection:
    """Read model projection for a visual meeting room."""
    meeting_id: str
    title: str
    room_name: str
    is_active: bool
    status: str
    purpose: str
    organizer_employee_id: str
    participant_employee_ids: list[str] = field(default_factory=list)
    active_decision_count: int = 0
    started_at: datetime | None = None


@dataclass
class OfficeProjectAreaProjection:
    """Read model projection for a visual project area."""
    project_id: str
    name: str
    status: str
    progress_percentage: float = 0.0
    total_requirements: int = 0
    completed_tasks: int = 0
    active_tasks: int = 0
    blocked_tasks: int = 0
    assigned_employee_ids: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HumanAttentionItem:
    """Represents an urgent organizational event requiring human review/action."""
    item_id: str
    attention_type: HumanAttentionType
    title: str
    description: str
    entity_id: str                          # e.g., approval_id, task_id, violation_id
    entity_type: str                        # "APPROVAL", "TASK", "VIOLATION", "EMERGENCY_STOP"
    severity: str = "HIGH"
    action_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class OfficeActivityItem:
    """Chronological activity log item projected from real domain events."""
    activity_id: str
    title: str
    description: str
    category: str                           # "TASK", "GOVERNANCE", "VERIFICATION", "RECOVERY", "MEETING", "TOOL"
    actor_id: str
    entity_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class OfficeCompanyProjection:
    """High-level real-time company overview projection."""
    company_name: str
    is_emergency_stopped: bool
    active_employees_count: int
    working_employees_count: int
    in_meeting_employees_count: int
    blocked_tasks_count: int
    pending_approvals_count: int
    active_projects_count: int
    failed_verifications_count: int
    active_recoveries_count: int = 0
    candidate_knowledge_count: int = 0
    validated_knowledge_count: int = 0
    authoritative_knowledge_count: int = 0
    contested_knowledge_count: int = 0
    stale_knowledge_count: int = 0
    active_experiments_count: int = 0
    company_operating_cycle_state: str = "COMPLETED"
    company_health_status: str = "HEALTHY"
    active_strategy_title: str = "Default Operating Strategy"
    attention_items: list[HumanAttentionItem] = field(default_factory=list)
    recent_activities: list[OfficeActivityItem] = field(default_factory=list)
    departments: list[DepartmentLayoutProjection] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
