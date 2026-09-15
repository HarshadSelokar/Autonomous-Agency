"""Pydantic Schemas for Phase 15 Dynamic Workforce and Team Formation APIs."""

from pydantic import BaseModel, Field


class CreateWorkforceDemandSchema(BaseModel):
    source_type: str = "PROJECT"
    source_id: str
    capability: str
    required_count: int = 1
    priority: int = 1
    department_id: str | None = None
    duration_days: int = 30
    deadline: str | None = None
    risk_level: str = "LOW"
    governance_required: bool = False


class WorkforceDemandResponseSchema(BaseModel):
    id: str
    source_type: str
    source_id: str
    department_id: str | None = None
    capability: str
    required_count: int
    priority: int
    duration_days: int
    deadline: str | None = None
    risk_level: str
    governance_required: bool
    created_at: str


class CapabilityGapResponseSchema(BaseModel):
    id: str
    capability: str
    required_count: int
    available_count: int
    gap_count: int
    severity: str
    affected_project_ids: list[str] = Field(default_factory=list)
    created_at: str


class GenerateRecommendationSchema(BaseModel):
    demand_id: str


class StaffingRecommendationResponseSchema(BaseModel):
    id: str
    demand_id: str
    candidate_employee_ids: list[str] = Field(default_factory=list)
    capability_fit_score: float
    availability_score: float
    workload_score: float
    reliability_score: float
    final_score: float
    reasoning: str
    created_at: str


class CreateTeamSchema(BaseModel):
    name: str
    code: str
    purpose: str = ""
    team_type: str = "TEMPORARY"
    project_id: str | None = None
    department_ids: list[str] = Field(default_factory=list)
    manager_id: str | None = None
    creation_reason: str = ""


class AddTeamMemberSchema(BaseModel):
    employee_id: str
    role_in_team: str = "MEMBER"
    allocation_percentage: float = 100.0


class TeamMemberResponseSchema(BaseModel):
    id: str
    team_id: str
    employee_id: str
    role_in_team: str
    allocation_percentage: float
    assigned_at: str
    removed_at: str | None = None


class TeamResponseSchema(BaseModel):
    id: str
    name: str
    code: str
    purpose: str
    team_type: str
    project_id: str | None = None
    department_ids: list[str] = Field(default_factory=list)
    manager_id: str | None = None
    status: str
    capabilities: list[str] = Field(default_factory=list)
    creation_reason: str
    created_at: str
    dissolved_at: str | None = None
    members: list[TeamMemberResponseSchema] = Field(default_factory=list)


class RequestWorkforceChangeSchema(BaseModel):
    request_type: str  # e.g., CREATE_TEAM, FORM_TEAM, REALLOCATE_EMPLOYEE, REQUEST_NEW_EMPLOYEE
    target_id: str
    requested_by_id: str
    justification: str


class WorkforceChangeRequestResponseSchema(BaseModel):
    id: str
    request_type: str
    target_id: str
    requested_by_id: str
    justification: str
    governance_approval_id: str | None = None
    status: str
    created_at: str
    processed_at: str | None = None


class ApproveWorkforceChangeSchema(BaseModel):
    actor_id: str
    governance_approval_id: str | None = None
    is_human_approval: bool = False
    reason: str = "Approved"


class WorkforceHealthResponseSchema(BaseModel):
    status: str
    total_active_employees: int
    active_teams_count: int
    open_capability_gaps: int
    unmet_demand_count: int
    overloaded_employee_count: int
