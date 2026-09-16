"""Pydantic Schemas for Phase 14 Department Expansion and Cross-Department Collaboration APIs."""


from pydantic import BaseModel, Field


class CreateDepartmentSchema(BaseModel):
    id: str | None = None
    name: str
    code: str
    description: str = ""
    purpose: str = ""
    parent_department_id: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


class UpdateDepartmentStatusSchema(BaseModel):
    status: str
    reason: str | None = None


class AssignDepartmentManagerSchema(BaseModel):
    manager_employee_id: str


class DepartmentResponseSchema(BaseModel):
    id: str
    name: str
    code: str
    description: str
    status: str
    purpose: str
    manager_employee_id: str | None = None
    parent_department_id: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class DepartmentHealthReportSchema(BaseModel):
    department_id: str
    health: str
    reason: str
    downstream_blocked_count: int = 0
    active_tasks: int = 0
    blocked_tasks: int = 0


class CreateDepartmentRequestSchema(BaseModel):
    requester_department_id: str
    receiving_department_id: str
    requester_employee_id: str
    purpose: str
    requested_outcome: str
    priority: str = "MEDIUM"
    sla_deadline: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    related_objective_id: str | None = None
    related_project_id: str | None = None


class AcceptDepartmentRequestSchema(BaseModel):
    receiving_manager_id: str
    delivery_owner_employee_id: str


class RejectDepartmentRequestSchema(BaseModel):
    receiving_manager_id: str
    reason: str


class DepartmentRequestResponseSchema(BaseModel):
    request_id: str
    requester_department_id: str
    receiving_department_id: str
    requester_employee_id: str
    receiving_manager_id: str
    delivery_owner_employee_id: str | None = None
    purpose: str
    requested_outcome: str
    priority: str
    status: str
    rejection_reason: str | None = None
    created_at: str
    updated_at: str


class SubmitDepartmentHandoffSchema(BaseModel):
    sender_employee_id: str
    expected_outcome: str
    artifact_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)


class VerifyDepartmentHandoffSchema(BaseModel):
    verifier_employee_id: str
    is_approved: bool = True
    reason: str | None = None


class DepartmentHandoffResponseSchema(BaseModel):
    handoff_id: str
    request_id: str
    sender_department_id: str
    receiver_department_id: str
    sender_employee_id: str
    expected_outcome: str
    status: str
    is_verified: bool
    rejection_reason: str | None = None
    created_at: str
