"""
Pydantic Schemas for Phase 11 Human Governance REST APIs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GovernanceRuleSchema(BaseModel):
    rule_id: str
    name: str
    description: str
    scope: str = "COMPANY"
    target_pattern: str
    min_risk_level: str = "MEDIUM"
    autonomy_level: str = "APPROVAL_REQUIRED"
    required_approver_roles: List[str] = Field(default_factory=list)
    prohibit_self_approval: bool = True
    approval_validity_seconds: int = 3600
    allow_override: bool = True


class GovernancePolicyCreateSchema(BaseModel):
    name: str
    scope: str = "COMPANY"
    scope_id: Optional[str] = None
    level: str = "COMPANY"
    rules: List[GovernanceRuleSchema] = Field(default_factory=list)


class GovernanceApprovalRequestCreateSchema(BaseModel):
    action_type: str
    action_target: str
    requested_by_actor_id: str
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    risk_level: str = "HIGH"
    required_approver_roles: Optional[List[str]] = None
    prohibit_self_approval: bool = True
    validity_seconds: int = 3600
    payload: Dict[str, Any] = Field(default_factory=dict)


class GovernanceApprovalDecisionSchema(BaseModel):
    actor_id: str
    reason: Optional[str] = None


class HumanInterventionRequestSchema(BaseModel):
    intervention_type: str                  # "PAUSE", "RESUME", "REJECT", "OVERRIDE", "CANCEL", "REWORK"
    scope: str = "COMPANY"
    scope_id: str = "COMPANY"
    actor_id: str
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


class EmergencyStopRequestSchema(BaseModel):
    activated_by_actor_id: str
    reason: str
    scope: str = "GLOBAL"
    scope_id: str = "GLOBAL"


class GovernanceOverrideRequestSchema(BaseModel):
    action_id: str
    policy_id: str
    actor_id: str
    reason: str
    previous_autonomy_level: str
    override_autonomy_level: str


class GovernanceApprovalResponseSchema(BaseModel):
    request_id: str
    action_type: str
    action_target: str
    requested_by_actor_id: str
    task_id: Optional[str] = None
    risk_level: str
    status: str
    approved_by_actor_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str


class PolicyViolationResponseSchema(BaseModel):
    violation_id: str
    category: str
    summary: str
    actor_id: str
    task_id: Optional[str] = None
    severity: str
    created_at: str
