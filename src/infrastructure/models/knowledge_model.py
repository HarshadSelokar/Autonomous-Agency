"""SQLAlchemy ORM Models for Phase 18 Institutional Knowledge, Claims, Provenance, Validations, Conflicts, Relationships, Procedures, Experiments, and Usage Records."""

import json
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.experiment import ExperimentStatus, OrganizationalExperiment
from src.domain.knowledge import (
    ConflictStatus,
    KnowledgeAuthority,
    KnowledgeClaim,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeProcedure,
    KnowledgeProvenance,
    KnowledgeRelationship,
    KnowledgeScope,
    KnowledgeStatus,
    KnowledgeType,
    KnowledgeUsageRecord,
    KnowledgeValidation,
    RelationshipType,
)
from src.infrastructure.database import Base


class KnowledgeItemModel(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    knowledge_type: Mapped[str] = mapped_column(String(64), nullable=False, default="FACT", index=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPANY", index=True)
    scope_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    authority: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED", index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CANDIDATE", index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeItem:
        return KnowledgeItem(
            id=self.id,
            statement=self.statement,
            summary=self.summary,
            knowledge_type=KnowledgeType(self.knowledge_type),
            scope=KnowledgeScope(self.scope),
            scope_id=self.scope_id,
            authority=KnowledgeAuthority(self.authority),
            status=KnowledgeStatus(self.status),
            confidence=self.confidence,
            quality_score=self.quality_score,
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            observed_at=self.observed_at,
            superseded_at=self.superseded_at,
            version=self.version,
            owner_id=self.owner_id,
            metadata=json.loads(self.metadata_json) if self.metadata_json else {},
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeItem) -> "KnowledgeItemModel":
        return cls(
            id=entity.id,
            statement=entity.statement,
            summary=entity.summary,
            knowledge_type=entity.knowledge_type.value if isinstance(entity.knowledge_type, Enum) else str(entity.knowledge_type),
            scope=entity.scope.value if isinstance(entity.scope, Enum) else str(entity.scope),
            scope_id=entity.scope_id,
            authority=entity.authority.value if isinstance(entity.authority, Enum) else str(entity.authority),
            status=entity.status.value if isinstance(entity.status, Enum) else str(entity.status),
            confidence=entity.confidence,
            quality_score=entity.quality_score,
            valid_from=entity.valid_from,
            valid_until=entity.valid_until,
            observed_at=entity.observed_at,
            superseded_at=entity.superseded_at,
            version=entity.version,
            owner_id=entity.owner_id,
            metadata_json=json.dumps(entity.metadata),
            created_at=entity.created_at,
        )


class KnowledgeClaimModel(Base):
    __tablename__ = "knowledge_claims"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    claim_scope: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPANY")
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="TASK_EXECUTION")
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    authority: Mapped[str] = mapped_column(String(32), nullable=False, default="UNVERIFIED")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CANDIDATE")
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeClaim:
        return KnowledgeClaim(
            id=self.id,
            knowledge_id=self.knowledge_id,
            statement=self.statement,
            claim_scope=KnowledgeScope(self.claim_scope),
            source_type=self.source_type,
            source_id=self.source_id,
            evidence_ids=json.loads(self.evidence_ids_json) if self.evidence_ids_json else [],
            confidence=self.confidence,
            authority=KnowledgeAuthority(self.authority),
            status=KnowledgeStatus(self.status),
            valid_until=self.valid_until,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeClaim) -> "KnowledgeClaimModel":
        return cls(
            id=entity.id,
            knowledge_id=entity.knowledge_id,
            statement=entity.statement,
            claim_scope=entity.claim_scope.value if isinstance(entity.claim_scope, Enum) else str(entity.claim_scope),
            source_type=entity.source_type,
            source_id=entity.source_id,
            evidence_ids_json=json.dumps(entity.evidence_ids),
            confidence=entity.confidence,
            authority=entity.authority.value if isinstance(entity.authority, Enum) else str(entity.authority),
            status=entity.status.value if isinstance(entity.status, Enum) else str(entity.status),
            valid_until=entity.valid_until,
            created_at=entity.created_at,
        )


class KnowledgeProvenanceModel(Base):
    __tablename__ = "knowledge_provenances"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="TASK")
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    objective_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meeting_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verification_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    memory_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeProvenance:
        return KnowledgeProvenance(
            id=self.id,
            knowledge_id=self.knowledge_id,
            source_type=self.source_type,
            source_id=self.source_id,
            employee_id=self.employee_id,
            agent_id=self.agent_id,
            task_id=self.task_id,
            project_id=self.project_id,
            objective_id=self.objective_id,
            decision_id=self.decision_id,
            meeting_id=self.meeting_id,
            artifact_id=self.artifact_id,
            verification_id=self.verification_id,
            outcome_id=self.outcome_id,
            memory_id=self.memory_id,
            analysis_id=self.analysis_id,
            timestamp=self.timestamp,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeProvenance) -> "KnowledgeProvenanceModel":
        return cls(
            id=entity.id,
            knowledge_id=entity.knowledge_id,
            source_type=entity.source_type,
            source_id=entity.source_id,
            employee_id=entity.employee_id,
            agent_id=entity.agent_id,
            task_id=entity.task_id,
            project_id=entity.project_id,
            objective_id=entity.objective_id,
            decision_id=entity.decision_id,
            meeting_id=entity.meeting_id,
            artifact_id=entity.artifact_id,
            verification_id=entity.verification_id,
            outcome_id=entity.outcome_id,
            memory_id=entity.memory_id,
            analysis_id=entity.analysis_id,
            timestamp=entity.timestamp,
        )


class KnowledgeValidationModel(Base):
    __tablename__ = "knowledge_validations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    validator_id: Mapped[str] = mapped_column(String(64), nullable=False, default="system_validator")
    validator_type: Mapped[str] = mapped_column(String(64), nullable=False, default="DETERMINISTIC_VERIFICATION")
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PASSED")
    confidence_delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeValidation:
        return KnowledgeValidation(
            id=self.id,
            knowledge_id=self.knowledge_id,
            validator_id=self.validator_id,
            validator_type=self.validator_type,
            evidence_ids=json.loads(self.evidence_ids_json) if self.evidence_ids_json else [],
            validation_status=self.validation_status,
            confidence_delta=self.confidence_delta,
            rationale=self.rationale,
            timestamp=self.timestamp,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeValidation) -> "KnowledgeValidationModel":
        return cls(
            id=entity.id,
            knowledge_id=entity.knowledge_id,
            validator_id=entity.validator_id,
            validator_type=entity.validator_type,
            evidence_ids_json=json.dumps(entity.evidence_ids),
            validation_status=entity.validation_status,
            confidence_delta=entity.confidence_delta,
            rationale=entity.rationale,
            timestamp=entity.timestamp,
        )


class KnowledgeConflictModel(Base):
    __tablename__ = "knowledge_conflicts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_id_a: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    knowledge_id_b: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    conflict_type: Mapped[str] = mapped_column(String(64), nullable=False, default="CONTRADICTORY_STATEMENT")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    resolution_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeConflict:
        return KnowledgeConflict(
            id=self.id,
            knowledge_id_a=self.knowledge_id_a,
            knowledge_id_b=self.knowledge_id_b,
            conflict_type=self.conflict_type,
            description=self.description,
            status=ConflictStatus(self.status),
            resolution_strategy=self.resolution_strategy,
            resolved_by_id=self.resolved_by_id,
            resolved_at=self.resolved_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeConflict) -> "KnowledgeConflictModel":
        return cls(
            id=entity.id,
            knowledge_id_a=entity.knowledge_id_a,
            knowledge_id_b=entity.knowledge_id_b,
            conflict_type=entity.conflict_type,
            description=entity.description,
            status=entity.status.value if isinstance(entity.status, Enum) else str(entity.status),
            resolution_strategy=entity.resolution_strategy,
            resolved_by_id=entity.resolved_by_id,
            resolved_at=entity.resolved_at,
            created_at=entity.created_at,
        )


class KnowledgeRelationshipModel(Base):
    __tablename__ = "knowledge_relationships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="KNOWLEDGE")
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False, default="KNOWLEDGE")
    target_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False, default="LEADS_TO_LESSON", index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeRelationship:
        return KnowledgeRelationship(
            id=self.id,
            source_type=self.source_type,
            source_id=self.source_id,
            target_type=self.target_type,
            target_id=self.target_id,
            relationship_type=RelationshipType(self.relationship_type),
            weight=self.weight,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeRelationship) -> "KnowledgeRelationshipModel":
        return cls(
            id=entity.id,
            source_type=entity.source_type,
            source_id=entity.source_id,
            target_type=entity.target_type,
            target_id=entity.target_id,
            relationship_type=entity.relationship_type.value if isinstance(entity.relationship_type, Enum) else str(entity.relationship_type),
            weight=entity.weight,
            created_at=entity.created_at,
        )


class KnowledgeProcedureModel(Base):
    __tablename__ = "knowledge_procedures"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False, default="")
    prerequisites_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    steps_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False, default="")
    verification_criteria_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    failure_conditions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    rollback_steps_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPANY")
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="CANDIDATE")
    is_governance_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeProcedure:
        return KnowledgeProcedure(
            id=self.id,
            title=self.title,
            purpose=self.purpose,
            prerequisites=json.loads(self.prerequisites_json) if self.prerequisites_json else [],
            steps=json.loads(self.steps_json) if self.steps_json else [],
            expected_outcome=self.expected_outcome,
            verification_criteria=json.loads(self.verification_criteria_json) if self.verification_criteria_json else [],
            failure_conditions=json.loads(self.failure_conditions_json) if self.failure_conditions_json else [],
            rollback_steps=json.loads(self.rollback_steps_json) if self.rollback_steps_json else [],
            scope=KnowledgeScope(self.scope),
            owner_id=self.owner_id,
            version=self.version,
            validation_status=KnowledgeStatus(self.validation_status),
            is_governance_approved=self.is_governance_approved,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeProcedure) -> "KnowledgeProcedureModel":
        return cls(
            id=entity.id,
            title=entity.title,
            purpose=entity.purpose,
            prerequisites_json=json.dumps(entity.prerequisites),
            steps_json=json.dumps(entity.steps),
            expected_outcome=entity.expected_outcome,
            verification_criteria_json=json.dumps(entity.verification_criteria),
            failure_conditions_json=json.dumps(entity.failure_conditions),
            rollback_steps_json=json.dumps(entity.rollback_steps),
            scope=entity.scope.value if isinstance(entity.scope, Enum) else str(entity.scope),
            owner_id=entity.owner_id,
            version=entity.version,
            validation_status=entity.validation_status.value if isinstance(entity.validation_status, Enum) else str(entity.validation_status),
            is_governance_approved=entity.is_governance_approved,
            created_at=entity.created_at,
        )


class OrganizationalExperimentModel(Base):
    __tablename__ = "organizational_experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    objective_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPANY")
    scope_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    baseline_metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    treatment_params_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    success_criteria_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    results_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    conclusion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_isolated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    governance_approval_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> OrganizationalExperiment:
        return OrganizationalExperiment(
            id=self.id,
            title=self.title,
            hypothesis=self.hypothesis,
            objective_id=self.objective_id,
            scope=self.scope,
            scope_id=self.scope_id,
            baseline_metrics=json.loads(self.baseline_metrics_json) if self.baseline_metrics_json else {},
            treatment_params=json.loads(self.treatment_params_json) if self.treatment_params_json else {},
            success_criteria=json.loads(self.success_criteria_json) if self.success_criteria_json else {},
            risk_level=self.risk_level,
            duration_hours=self.duration_hours,
            status=ExperimentStatus(self.status),
            results=json.loads(self.results_json) if self.results_json else {},
            conclusion=self.conclusion,
            is_isolated=self.is_isolated,
            governance_approval_id=self.governance_approval_id,
            started_at=self.started_at,
            completed_at=self.completed_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: OrganizationalExperiment) -> "OrganizationalExperimentModel":
        return cls(
            id=entity.id,
            title=entity.title,
            hypothesis=entity.hypothesis,
            objective_id=entity.objective_id,
            scope=entity.scope,
            scope_id=entity.scope_id,
            baseline_metrics_json=json.dumps(entity.baseline_metrics),
            treatment_params_json=json.dumps(entity.treatment_params),
            success_criteria_json=json.dumps(entity.success_criteria),
            risk_level=entity.risk_level,
            duration_hours=entity.duration_hours,
            status=entity.status.value if isinstance(entity.status, Enum) else str(entity.status),
            results_json=json.dumps(entity.results),
            conclusion=entity.conclusion,
            is_isolated=entity.is_isolated,
            governance_approval_id=entity.governance_approval_id,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
        )


class KnowledgeUsageRecordModel(Base):
    __tablename__ = "knowledge_usage_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    consumer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    context_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="TASK_EXECUTION")
    outcome_status: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCESS")
    effectiveness_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> KnowledgeUsageRecord:
        return KnowledgeUsageRecord(
            id=self.id,
            knowledge_id=self.knowledge_id,
            consumer_id=self.consumer_id,
            task_id=self.task_id,
            context_scope=self.context_scope,
            outcome_status=self.outcome_status,
            effectiveness_score=self.effectiveness_score,
            timestamp=self.timestamp,
        )

    @classmethod
    def from_domain(cls, entity: KnowledgeUsageRecord) -> "KnowledgeUsageRecordModel":
        return cls(
            id=entity.id,
            knowledge_id=entity.knowledge_id,
            consumer_id=entity.consumer_id,
            task_id=entity.task_id,
            context_scope=entity.context_scope,
            outcome_status=entity.outcome_status,
            effectiveness_score=entity.effectiveness_score,
            timestamp=entity.timestamp,
        )
