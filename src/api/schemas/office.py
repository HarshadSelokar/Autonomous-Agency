"""Pydantic Schemas for Phase 13 Pixel Office API."""

from pydantic import BaseModel, Field


class WorkstationProjectionSchema(BaseModel):
    employee_id: str
    employee_name: str
    employee_title: str
    role: str
    department_id: str | None = None
    manager_id: str | None = None
    desk_id: str
    area_type: str
    visual_state: str
    current_task_id: str | None = None
    current_task_title: str | None = None
    current_project_id: str | None = None
    current_project_name: str | None = None
    current_activity_summary: str = "Idle"
    active_agent_id: str | None = None
    active_tool_name: str | None = None
    active_model_id: str | None = None
    is_manager: bool = False
    updated_at: str


class DepartmentLayoutProjectionSchema(BaseModel):
    department_id: str
    name: str
    area_type: str
    head_employee_id: str | None = None
    total_desks: int = 10
    occupied_desks: int = 0
    active_employee_ids: list[str] = Field(default_factory=list)


class OfficeMeetingRoomProjectionSchema(BaseModel):
    meeting_id: str
    title: str
    room_name: str
    is_active: bool
    status: str
    purpose: str
    organizer_employee_id: str
    participant_employee_ids: list[str] = Field(default_factory=list)
    active_decision_count: int = 0
    started_at: str | None = None


class OfficeProjectAreaProjectionSchema(BaseModel):
    project_id: str
    name: str
    status: str
    progress_percentage: float = 0.0
    total_requirements: int = 0
    completed_tasks: int = 0
    active_tasks: int = 0
    blocked_tasks: int = 0
    assigned_employee_ids: list[str] = Field(default_factory=list)
    updated_at: str


class HumanAttentionItemSchema(BaseModel):
    item_id: str
    attention_type: str
    title: str
    description: str
    entity_id: str
    entity_type: str
    severity: str = "HIGH"
    action_url: str | None = None
    created_at: str


class OfficeActivityItemSchema(BaseModel):
    activity_id: str
    title: str
    description: str
    category: str
    actor_id: str
    entity_id: str
    timestamp: str


class OfficeCompanyOverviewSchema(BaseModel):
    company_name: str
    is_emergency_stopped: bool
    active_employees_count: int
    working_employees_count: int
    in_meeting_employees_count: int
    blocked_tasks_count: int
    pending_approvals_count: int
    active_projects_count: int
    active_recoveries_count: int = 0
    candidate_knowledge_count: int = 0
    validated_knowledge_count: int = 0
    authoritative_knowledge_count: int = 0
    contested_knowledge_count: int = 0
    stale_knowledge_count: int = 0
    active_experiments_count: int = 0
    active_research_programs_count: int = 0
    pending_research_requests_count: int = 0
    research_discoveries_count: int = 0
    innovation_proposals_count: int = 0
    attention_items: list[HumanAttentionItemSchema] = Field(default_factory=list)
    recent_activities: list[OfficeActivityItemSchema] = Field(default_factory=list)
    updated_at: str
