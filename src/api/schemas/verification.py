"""
Pydantic Schemas for Phase 10 Verification and Recovery REST APIs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VerificationRuleSchema(BaseModel):
    rule_id: str
    rule_type: str
    name: str
    description: str
    target: str
    expected_condition: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "CRITICAL"
    retryable: bool = True
    requires_human: bool = False
    min_trust_level: str = "EXECUTED"


class ExpectedOutcomeCreateSchema(BaseModel):
    task_id: str
    description: str
    criteria: List[str] = Field(default_factory=list)
    rules: List[VerificationRuleSchema] = Field(default_factory=list)
    required_evidence_types: List[str] = Field(default_factory=list)
    policy: Dict[str, Any] = Field(default_factory=dict)


class VerificationEvidenceCreateSchema(BaseModel):
    source_type: str
    source_id: str
    task_id: Optional[str] = None
    workspace_id: Optional[str] = None
    trust_level: str = "EXECUTED"
    checksum: Optional[str] = None
    commit_sha: Optional[str] = None
    artifact_version: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class VerifyTaskRequestSchema(BaseModel):
    task_id: str
    evidence_ids: Optional[List[str]] = None


class HumanOverrideRequestSchema(BaseModel):
    actor_id: str
    reason: str
    waive: bool = False


class VerificationResponseSchema(BaseModel):
    verification_id: str
    task_id: str
    outcome_id: str
    status: str
    summary: str
    recommended_recovery: Optional[str] = None
    is_human_verified: bool = False
    verified_by_actor_id: Optional[str] = None
    override_reason: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)


class FailureRecordResponseSchema(BaseModel):
    failure_id: str
    task_id: str
    category: str
    severity: str
    summary: str
    details: Dict[str, Any]
    retryable: bool
    recommended_strategy: Optional[str]
    created_at: str


class RecoveryActionResponseSchema(BaseModel):
    action_id: str
    failure_id: str
    task_id: str
    strategy: str
    attempt_number: int
    success: bool
    executed_by: str
    created_at: str
