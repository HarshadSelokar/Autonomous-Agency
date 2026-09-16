"""
Verification Domain Entities and Value Objects for Phase 10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    COLLECTING_EVIDENCE = "COLLECTING_EVIDENCE"
    CHECKING = "CHECKING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    WAIVED = "WAIVED"
    CANCELLED = "CANCELLED"


class EvidenceTrustLevel(str, Enum):
    UNTRUSTED = "UNTRUSTED"        # Agent claim or unverified text assertion
    OBSERVED = "OBSERVED"          # System log or external observation
    EXECUTED = "EXECUTED"          # Recorded tool execution result
    VALIDATED = "VALIDATED"        # System validation check outcome
    AUTHORIZED = "AUTHORIZED"      # Code review / Manager / Decision authorization
    AUTHORITATIVE = "AUTHORITATIVE" # Independent verifier execution / Signed cryptographic artifact


class VerificationType(str, Enum):
    STATE_VERIFICATION = "STATE_VERIFICATION"
    ARTIFACT_VERIFICATION = "ARTIFACT_VERIFICATION"
    TOOL_EXECUTION_VERIFICATION = "TOOL_EXECUTION_VERIFICATION"
    TEST_VERIFICATION = "TEST_VERIFICATION"
    FILE_VERIFICATION = "FILE_VERIFICATION"
    SCHEMA_VERIFICATION = "SCHEMA_VERIFICATION"
    API_VERIFICATION = "API_VERIFICATION"
    GIT_VERIFICATION = "GIT_VERIFICATION"
    HUMAN_VERIFICATION = "HUMAN_VERIFICATION"
    COMPOSITE_VERIFICATION = "COMPOSITE_VERIFICATION"


class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"  # Fails verification immediately
    WARNING = "WARNING"    # Soft failure, recorded but does not fail task
    INFO = "INFO"          # Informational check


@dataclass
class VerificationEvidence:
    """Represents a piece of evidence supporting or refuting a verification rule."""
    evidence_id: str
    source_type: str        # e.g., "AgentRun", "ToolExecution", "TestRun", "CodeReview", "Artifact", "GitCommit"
    source_id: str
    task_id: str | None = None
    workspace_id: str | None = None
    agent_run_id: str | None = None
    employee_id: str | None = None
    tool_execution_id: str | None = None
    artifact_id: str | None = None
    trust_level: EvidenceTrustLevel = EvidenceTrustLevel.UNTRUSTED
    checksum: str | None = None
    commit_sha: str | None = None
    artifact_version: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_trusted_at_least(self, min_level: EvidenceTrustLevel) -> bool:
        hierarchy = [
            EvidenceTrustLevel.UNTRUSTED,
            EvidenceTrustLevel.OBSERVED,
            EvidenceTrustLevel.EXECUTED,
            EvidenceTrustLevel.VALIDATED,
            EvidenceTrustLevel.AUTHORIZED,
            EvidenceTrustLevel.AUTHORITATIVE,
        ]
        return hierarchy.index(self.trust_level) >= hierarchy.index(min_level)


@dataclass
class VerificationRule:
    """Defines a rule to evaluate during verification."""
    rule_id: str
    rule_type: VerificationType
    name: str
    description: str
    target: str                           # e.g. file path, artifact name, test command, endpoint URL
    expected_condition: dict[str, Any]    # e.g. {"exists": True, "exit_code": 0, "status": "APPROVED"}
    severity: RuleSeverity = RuleSeverity.CRITICAL
    retryable: bool = True
    requires_human: bool = False
    min_trust_level: EvidenceTrustLevel = EvidenceTrustLevel.EXECUTED
    operator: str = "AND"                 # For composite rules: "AND", "OR", "NOT"
    sub_rules: list[VerificationRule] = field(default_factory=list)


@dataclass
class ExpectedOutcome:
    """Structured representation of what a task must accomplish to be verified."""
    outcome_id: str
    task_id: str
    description: str
    criteria: list[str]
    rules: list[VerificationRule]
    required_evidence_types: list[str] = field(default_factory=list)
    completion_conditions: dict[str, Any] = field(default_factory=dict)
    failure_conditions: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VerificationCheckResult:
    """Outcome of evaluating a single VerificationRule."""
    check_id: str
    rule_id: str
    rule_name: str
    rule_type: VerificationType
    severity: RuleSeverity
    passed: bool
    evidence_ids: list[str] = field(default_factory=list)
    reason: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VerificationResult:
    """Aggregate result produced by the VerificationEngine."""
    verification_id: str
    task_id: str
    outcome_id: str
    status: VerificationStatus
    passed_checks: list[VerificationCheckResult] = field(default_factory=list)
    failed_checks: list[VerificationCheckResult] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    summary: str = ""
    recommended_recovery: str | None = None
    is_human_verified: bool = False
    verified_by_actor_id: str | None = None
    override_reason: str | None = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_verified(self) -> bool:
        return self.status == VerificationStatus.VERIFIED or self.status == VerificationStatus.WAIVED


@dataclass
class VerificationAttempt:
    """Tracks a single verification execution attempt."""
    attempt_id: str
    verification_id: str
    task_id: str
    attempt_number: int
    status: VerificationStatus
    result: VerificationResult | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
