"""
Repository implementation for Phase 10 Verification and Recovery entities.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.verification import (
    ExpectedOutcome,
    EvidenceTrustLevel,
    VerificationEvidence,
    VerificationResult,
    VerificationStatus,
)
from src.domain.recovery import (
    FailureCategory,
    FailureRecord,
    RecoveryAction,
    RecoveryStrategy,
)
from src.infrastructure.models.verification_model import (
    ExpectedOutcomeModel,
    FailureRecordModel,
    RecoveryActionModel,
    VerificationEvidenceModel,
    VerificationModel,
)


class VerificationRepository:
    def __init__(self, session: Session):
        self._session = session

    def save_outcome(self, outcome: ExpectedOutcome) -> ExpectedOutcome:
        rules_dict = [
            {
                "rule_id": r.rule_id,
                "rule_type": r.rule_type.value,
                "name": r.name,
                "description": r.description,
                "target": r.target,
                "expected_condition": r.expected_condition,
                "severity": r.severity.value,
                "retryable": r.retryable,
                "requires_human": r.requires_human,
                "min_trust_level": r.min_trust_level.value,
                "operator": r.operator,
            }
            for r in outcome.rules
        ]
        model = ExpectedOutcomeModel(
            id=outcome.outcome_id,
            task_id=outcome.task_id,
            description=outcome.description,
            criteria=outcome.criteria,
            rules_data=rules_dict,
            required_evidence_types=outcome.required_evidence_types,
            completion_conditions=outcome.completion_conditions,
            failure_conditions=outcome.failure_conditions,
            policy=outcome.policy,
            created_at=outcome.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return outcome

    def get_outcome(self, outcome_id: str) -> Optional[ExpectedOutcomeModel]:
        stmt = select(ExpectedOutcomeModel).where(ExpectedOutcomeModel.id == outcome_id)
        return self._session.scalars(stmt).first()

    def get_outcome_by_task(self, task_id: str) -> Optional[ExpectedOutcomeModel]:
        stmt = select(ExpectedOutcomeModel).where(ExpectedOutcomeModel.task_id == task_id)
        return self._session.scalars(stmt).first()

    def save_verification(self, result: VerificationResult) -> VerificationResult:
        model = VerificationModel(
            id=result.verification_id,
            task_id=result.task_id,
            outcome_id=result.outcome_id,
            status=result.status.value if hasattr(result.status, "value") else str(result.status),
            summary=result.summary,
            recommended_recovery=result.recommended_recovery,
            is_human_verified=result.is_human_verified,
            verified_by_actor_id=result.verified_by_actor_id,
            override_reason=result.override_reason,
            evidence_ids=result.evidence_ids,
            created_at=result.evaluated_at,
            updated_at=result.evaluated_at,
        )
        self._session.merge(model)
        self._session.commit()
        return result

    def get_verification(self, verification_id: str) -> Optional[VerificationModel]:
        stmt = select(VerificationModel).where(VerificationModel.id == verification_id)
        return self._session.scalars(stmt).first()

    def get_verifications_by_task(self, task_id: str) -> List[VerificationModel]:
        stmt = select(VerificationModel).where(VerificationModel.task_id == task_id).order_by(VerificationModel.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def save_evidence(self, evidence: VerificationEvidence) -> VerificationEvidence:
        model = VerificationEvidenceModel(
            id=evidence.evidence_id,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            task_id=evidence.task_id,
            workspace_id=evidence.workspace_id,
            agent_run_id=evidence.agent_run_id,
            employee_id=evidence.employee_id,
            tool_execution_id=evidence.tool_execution_id,
            artifact_id=evidence.artifact_id,
            trust_level=evidence.trust_level.value if hasattr(evidence.trust_level, "value") else str(evidence.trust_level),
            checksum=evidence.checksum,
            commit_sha=evidence.commit_sha,
            artifact_version=evidence.artifact_version,
            payload=evidence.payload,
            created_at=evidence.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return evidence

    def get_evidence(self, evidence_id: str) -> Optional[VerificationEvidenceModel]:
        stmt = select(VerificationEvidenceModel).where(VerificationEvidenceModel.id == evidence_id)
        return self._session.scalars(stmt).first()

    def get_evidence_by_task(self, task_id: str) -> List[VerificationEvidenceModel]:
        stmt = select(VerificationEvidenceModel).where(VerificationEvidenceModel.task_id == task_id)
        return list(self._session.scalars(stmt).all())

    def save_failure(self, failure: FailureRecord) -> FailureRecord:
        model = FailureRecordModel(
            id=failure.failure_id,
            task_id=failure.task_id,
            verification_id=failure.verification_id,
            category=failure.category.value if hasattr(failure.category, "value") else str(failure.category),
            severity=failure.severity,
            summary=failure.summary,
            details=failure.details,
            retryable=failure.retryable,
            recoverable=failure.recoverable,
            recommended_strategy=failure.recommended_strategy.value if failure.recommended_strategy and hasattr(failure.recommended_strategy, "value") else failure.recommended_strategy,
            agent_id=failure.agent_id,
            employee_id=failure.employee_id,
            execution_id=failure.execution_id,
            evidence_ids=failure.evidence_ids,
            created_at=failure.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return failure

    def get_failures_by_task(self, task_id: str) -> List[FailureRecordModel]:
        stmt = select(FailureRecordModel).where(FailureRecordModel.task_id == task_id).order_by(FailureRecordModel.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def save_recovery_action(self, action: RecoveryAction) -> RecoveryAction:
        model = RecoveryActionModel(
            id=action.action_id,
            failure_id=action.failure_id,
            task_id=action.task_id,
            strategy=action.strategy.value if hasattr(action.strategy, "value") else str(action.strategy),
            attempt_number=action.attempt_number,
            success=action.success,
            details=action.details,
            executed_by=action.executed_by,
            created_at=action.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return action

    def get_recovery_actions_by_task(self, task_id: str) -> List[RecoveryActionModel]:
        stmt = select(RecoveryActionModel).where(RecoveryActionModel.task_id == task_id).order_by(RecoveryActionModel.created_at.asc())
        return list(self._session.scalars(stmt).all())
