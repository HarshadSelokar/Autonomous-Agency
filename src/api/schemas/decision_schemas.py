"""
Pydantic API Schemas for Organizational Decision Management.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CreateDecisionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    question: str = Field(..., min_length=1, max_length=512)
    decision_maker_employee_id: str = Field(..., min_length=1)
    description: str | None = None
    decision_type: str = "GENERAL"
    approving_authority_role: str | None = None
    chosen_option: str | None = None
    alternatives: list[str] = Field(default_factory=list)
    rationale: str | None = None
    consequences: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    meeting_id: str | None = None
    objective_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    provenance: str = "EMPLOYEE"


class ApproveDecisionRequest(BaseModel):
    approver_employee_id: str
    provenance: str | None = None


class RejectDecisionRequest(BaseModel):
    approver_employee_id: str
    reason: str


class SupersedeDecisionRequest(BaseModel):
    new_decision_id: str
    actor_employee_id: str


class DecisionResponse(BaseModel):
    id: str
    title: str
    question: str
    status: str
    decision_maker_employee_id: str
    decision_type: str
    approving_authority_role: str | None = None
    chosen_option: str | None = None
    alternatives: list[str]
    rationale: str | None = None
    meeting_id: str | None = None
    objective_id: str | None = None
    task_id: str | None = None
    previous_decision_id: str | None = None
    provenance: str
    created_at: datetime
    approved_at: datetime | None = None
