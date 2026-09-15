"""Pydantic schemas for Phase 14 Department API endpoints."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DepartmentCreateSchema(BaseModel):
    id: str
    name: str
    code: str
    description: str = ""
    purpose: str = ""
    responsibilities: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    manager_employee_id: Optional[str] = None
    parent_department_id: Optional[str] = None


class DepartmentUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    status: Optional[str] = None
    manager_employee_id: Optional[str] = None


class DepartmentResponseSchema(BaseModel):
    id: str
    name: str
    code: str
    description: str
    purpose: str
    status: str
    responsibilities: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    manager_employee_id: Optional[str] = None
    parent_department_id: Optional[str] = None
    created_at: str
    updated_at: str


class DepartmentRequestCreateSchema(BaseModel):
    receiving_department_id: str
    requester_employee_id: str
    purpose: str
    requested_outcome: str
    priority: str = "MEDIUM"
    required_capabilities: List[str] = Field(default_factory=list)
    related_objective_id: Optional[str] = None
    related_project_id: Optional[str] = None


class DepartmentRequestAcceptSchema(BaseModel):
    receiving_manager_id: str
    delivery_owner_employee_id: str


class DepartmentRequestRejectSchema(BaseModel):
    rejector_actor_id: str
    reason: str


class DepartmentRequestDeliverSchema(BaseModel):
    delivery_employee_id: str
    expected_outcome: str
    artifact_ids: List[str] = Field(default_factory=list)
    evidence_summary: str = ""


class DepartmentRequestVerifySchema(BaseModel):
    verifier_employee_id: str
    success: bool = True
    reason: Optional[str] = None


class DepartmentRequestResponseSchema(BaseModel):
    request_id: str
    requester_department_id: str
    receiving_department_id: str
    requester_employee_id: str
    purpose: str
    requested_outcome: str
    priority: str
    status: str
    accountable_manager_id: Optional[str] = None
    delivery_owner_employee_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str
    updated_at: str


class DepartmentMetricsResponseSchema(BaseModel):
    department_id: str
    active_task_count: int
    completed_task_count: int
    blocked_task_count: int
    incoming_request_count: int
    outgoing_request_count: int
    verification_failure_count: int
    recovery_attempt_count: int
    escalation_count: int
    health: str
    updated_at: str
