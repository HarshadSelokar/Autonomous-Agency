"""
Pydantic Schemas for Phase 10 Verification and Recovery REST APIs.
"""

from typing import Any

from pydantic import BaseModel, Field


class VerificationRuleSchema(BaseModel):
    rule_id: str
    rule_type: str
    name: str
    description: str
    target: str
    expected_condition: dict[str, Any] = Field(default_factory=dict)
    severity: str = "CRITICAL"
    retryable: bool = True
    requires_human: bool = False
    min_trust_level: str = "EXECUTED"


class ExpectedOutcomeCreateSchema(BaseModel):
    task_id: str
    description: str
    criteria: list[str] = Field(default_factory=list)
    rules: list[VerificationRuleSchema] = Field(default_factory=list)
    required_evidence_types: list[str] = Field(default_factory=list)
    policy: dict[str, Any] = Field(default_factory=dict)


class VerificationEvidenceCreateSchema(BaseModel):
    source_type: str
    source_id: str
    task_id: str | None = None
    workspace_id: str | None = None
    trust_level: str = "EXECUTED"
    checksum: str | None = None
    commit_sha: str | None = None
    artifact_version: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class VerifyTaskRequestSchema(BaseModel):
    task_id: str
    evidence_ids: list[str] | None = None


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
    recommended_recovery: str | None = None
    is_human_verified: bool = False
    verified_by_actor_id: str | None = None
    override_reason: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class FailureRecordResponseSchema(BaseModel):
    failure_id: str
    task_id: str
    category: str
    severity: str
    summary: str
    details: dict[str, Any]
    retryable: bool
    recommended_strategy: str | None
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
