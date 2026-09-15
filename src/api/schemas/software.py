"""
Pydantic Schemas for Phase 9 AI Software Company REST API.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CreateSoftwareProjectRequest(BaseModel):
    objective_id: str = Field(..., description="ID of associated Objective")
    name: str = Field(..., description="Project name")
    description: str = Field("", description="Project description")
    repository_path: str = Field("", description="Sandboxed workspace repository path")
    workspace_id: str = Field("", description="Sandboxed workspace ID")


class RequirementInput(BaseModel):
    title: str = Field(..., description="Requirement title")
    description: str = Field("", description="Requirement description")
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")


class AddRequirementsRequest(BaseModel):
    requirements: list[RequirementInput] = Field(..., min_length=1)


class SoftwareRequirementResponse(BaseModel):
    requirement_id: str
    project_id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: str
    status: str
    created_at: datetime


class SoftwareProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str
    objective_id: str
    repository_path: str
    workspace_id: str
    status: str
    created_at: datetime


class CreateEngineeringPlanRequest(BaseModel):
    manager_employee_id: str = Field(..., description="ID of Engineering Manager")
    architecture_overview: str = Field(..., description="Architecture overview specification")
    tech_stack: list[str] = Field(default_factory=list, description="List of technologies")


class EngineeringPlanResponse(BaseModel):
    plan_id: str
    project_id: str
    manager_employee_id: str
    architecture_overview: str
    tech_stack: list[str]
    task_ids: list[str]
    created_at: datetime


class SubmitCodeChangeRequest(BaseModel):
    project_id: str
    task_id: str
    author_employee_id: str
    files_changed: list[str]
    diff_summary: str
    agent_run_id: str = ""
    workspace_id: str = ""
    branch_name: str = "main"


class CodeChangeResponse(BaseModel):
    change_id: str
    project_id: str
    task_id: str
    author_employee_id: str
    branch_name: str
    files_changed: list[str]
    status: str
    commit_hash: str | None = None
    created_at: datetime


class RequestCodeReviewRequest(BaseModel):
    change_id: str
    reviewer_employee_id: str


class SubmitReviewFindingsRequest(BaseModel):
    status: str = Field(..., description="APPROVED or CHANGES_REQUESTED")
    findings: list[str] = Field(default_factory=list)
    recommendations: str = ""
    evidence_id: str | None = None


class CodeReviewResponse(BaseModel):
    review_id: str
    change_id: str
    reviewer_employee_id: str
    status: str
    findings: list[str]
    recommendations: str
    created_at: datetime


class RecordTestRunRequest(BaseModel):
    project_id: str
    task_id: str
    worker_employee_id: str
    command: str
    exit_code: int
    total_tests: int
    passed_count: int
    failed_count: int
    skipped_count: int = 0
    output_reference: str = ""
    agent_run_id: str = ""
    workspace_id: str = ""


class TestRunResponse(BaseModel):
    test_run_id: str
    project_id: str
    task_id: str
    worker_employee_id: str
    command: str
    exit_code: int
    total_tests: int
    passed_count: int
    failed_count: int
    status: str
    created_at: datetime


class ReportDefectRequest(BaseModel):
    title: str
    description: str = ""
    severity: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    reproduction_steps: str = ""
    originating_task_id: str | None = None
    assigned_employee_id: str | None = None


class SoftwareDefectResponse(BaseModel):
    defect_id: str
    project_id: str
    title: str
    severity: str
    status: str
    fix_task_id: str | None = None
    created_at: datetime


class RequestDeliveryRequest(BaseModel):
    requested_by_employee_id: str
    version: str = "1.0.0"
    commit_hash: str = "main"


class ApproveDeliveryRequest(BaseModel):
    approved_by_employee_id: str


class SoftwareDeliveryResponse(BaseModel):
    delivery_id: str
    project_id: str
    version: str
    commit_hash: str
    requested_by_employee_id: str
    approved_by_employee_id: str | None = None
    status: str
    evidence_summary: dict[str, Any]
    created_at: datetime
