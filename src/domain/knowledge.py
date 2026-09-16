"""
Institutional Knowledge Domain Module for Phase 18.

Defines entities, value objects, and enums for Institutional Knowledge, Knowledge Claims,
Provenance, Authority Lifecycles, Knowledge Validations, Conflicts, Relationships,
Versioned Procedures, and Usage Records.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid


class KnowledgeAuthority(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    OBSERVED = "OBSERVED"
    EVIDENCE_BACKED = "EVIDENCE_BACKED"
    VALIDATED = "VALIDATED"
    CONFIRMED = "CONFIRMED"
    AUTHORITATIVE = "AUTHORITATIVE"


class KnowledgeStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    UNDER_VALIDATION = "UNDER_VALIDATION"
    VALIDATED = "VALIDATED"
    CONFIRMED = "CONFIRMED"
    AUTHORITATIVE = "AUTHORITATIVE"
    SUPERSEDED = "SUPERSEDED"
    STALE = "STALE"
    CONTESTED = "CONTESTED"
    ARCHIVED = "ARCHIVED"
    INVALIDATED = "INVALIDATED"


class KnowledgeType(str, Enum):
    FACT = "FACT"
    LESSON = "LESSON"
    PATTERN = "PATTERN"
    PROCEDURAL = "PROCEDURAL"
    PREDICTION_LESSON = "PREDICTION_LESSON"
    DECISION_LESSON = "DECISION_LESSON"
    WORKFORCE_LESSON = "WORKFORCE_LESSON"
    TOOL_LESSON = "TOOL_LESSON"
    MODEL_LESSON = "MODEL_LESSON"
    STRATEGY_LESSON = "STRATEGY_LESSON"


class KnowledgeScope(str, Enum):
    COMPANY = "COMPANY"
    DEPARTMENT = "DEPARTMENT"
    PROJECT = "PROJECT"
    TEAM = "TEAM"
    EMPLOYEE = "EMPLOYEE"
    TASK = "TASK"
    TECHNOLOGY = "TECHNOLOGY"
    TOOL = "TOOL"
    MODEL = "MODEL"
    ENVIRONMENT = "ENVIRONMENT"


class ConflictStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"
    INCONCLUSIVE = "INCONCLUSIVE"


class RelationshipType(str, Enum):
    LEADS_TO_LESSON = "LEADS_TO_LESSON"
    EVIDENCE_FOR = "EVIDENCE_FOR"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    SUPERSEDES = "SUPERSEDES"
    DERIVED_FROM = "DERIVED_FROM"


@dataclass
class KnowledgeItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    statement: str = ""
    summary: str = ""
    knowledge_type: KnowledgeType = KnowledgeType.FACT
    scope: KnowledgeScope = KnowledgeScope.COMPANY
    scope_id: str | None = None
    authority: KnowledgeAuthority = KnowledgeAuthority.UNVERIFIED
    status: KnowledgeStatus = KnowledgeStatus.CANDIDATE
    confidence: float = 0.5
    quality_score: float = 0.5
    valid_from: datetime = field(default_factory=lambda: datetime.now(UTC))
    valid_until: datetime | None = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    superseded_at: datetime | None = None
    version: int = 1
    owner_id: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def promote_authority(self, target_authority: KnowledgeAuthority) -> None:
        authority_ranks = {
            KnowledgeAuthority.UNVERIFIED: 1,
            KnowledgeAuthority.OBSERVED: 2,
            KnowledgeAuthority.EVIDENCE_BACKED: 3,
            KnowledgeAuthority.VALIDATED: 4,
            KnowledgeAuthority.CONFIRMED: 5,
            KnowledgeAuthority.AUTHORITATIVE: 6,
        }
        if authority_ranks[target_authority] < authority_ranks[self.authority]:
            raise ValueError(f"Cannot demote authority from {self.authority} to {target_authority}")
        self.authority = target_authority
        if target_authority in (KnowledgeAuthority.VALIDATED, KnowledgeAuthority.CONFIRMED, KnowledgeAuthority.AUTHORITATIVE):
            self.status = KnowledgeStatus(target_authority.value) if target_authority.value in KnowledgeStatus.__members__ else self.status


@dataclass
class KnowledgeClaim:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = ""
    statement: str = ""
    claim_scope: KnowledgeScope = KnowledgeScope.COMPANY
    source_type: str = "TASK_EXECUTION"
    source_id: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.5
    authority: KnowledgeAuthority = KnowledgeAuthority.UNVERIFIED
    status: KnowledgeStatus = KnowledgeStatus.CANDIDATE
    valid_until: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeProvenance:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = ""
    source_type: str = "TASK"
    source_id: str = ""
    employee_id: str | None = None
    agent_id: str | None = None
    task_id: str | None = None
    project_id: str | None = None
    objective_id: str | None = None
    decision_id: str | None = None
    meeting_id: str | None = None
    artifact_id: str | None = None
    verification_id: str | None = None
    outcome_id: str | None = None
    memory_id: str | None = None
    analysis_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeValidation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = ""
    validator_id: str = "system_validator"
    validator_type: str = "DETERMINISTIC_VERIFICATION"  # DETERMINISTIC_VERIFICATION, HUMAN_GOVERNANCE, INDEPENDENT_TELEMETRY
    evidence_ids: list[str] = field(default_factory=list)
    validation_status: str = "PASSED"  # PASSED, FAILED, INCONCLUSIVE
    confidence_delta: float = 0.2
    rationale: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeConflict:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id_a: str = ""
    knowledge_id_b: str = ""
    conflict_type: str = "CONTRADICTORY_STATEMENT"
    description: str = ""
    status: ConflictStatus = ConflictStatus.OPEN
    resolution_strategy: str | None = None
    resolved_by_id: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeRelationship:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = "KNOWLEDGE"
    source_id: str = ""
    target_type: str = "KNOWLEDGE"
    target_id: str = ""
    relationship_type: RelationshipType = RelationshipType.LEADS_TO_LESSON
    weight: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeProcedure:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    purpose: str = ""
    prerequisites: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    expected_outcome: str = ""
    verification_criteria: list[str] = field(default_factory=list)
    failure_conditions: list[str] = field(default_factory=list)
    rollback_steps: list[str] = field(default_factory=list)
    scope: KnowledgeScope = KnowledgeScope.COMPANY
    owner_id: str = "system"
    version: int = 1
    validation_status: KnowledgeStatus = KnowledgeStatus.CANDIDATE
    is_governance_approved: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeUsageRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = ""
    consumer_id: str = ""
    task_id: str | None = None
    context_scope: str = "TASK_EXECUTION"
    outcome_status: str = "SUCCESS"  # SUCCESS, FAILURE, NEUTRAL
    effectiveness_score: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
