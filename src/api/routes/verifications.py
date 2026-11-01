"""
FastAPI Routes for Phase 10 Verification and Recovery.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas.verification import (
    ExpectedOutcomeCreateSchema,
    HumanOverrideRequestSchema,
    VerificationEvidenceCreateSchema,
    VerificationResponseSchema,
    VerifyTaskRequestSchema,
)
from src.application.recovery_engine import RecoveryEngine
from src.application.verification_engine import VerificationEngine
from src.domain.verification import (
    EvidenceTrustLevel,
    RuleSeverity,
    VerificationRule,
    VerificationType,
)
from src.infrastructure.database import get_db, run_with_sync_session
from src.infrastructure.repositories.verification_repository import VerificationRepository

router = APIRouter(prefix="/verifications", tags=["Verifications & Recovery"])


def _services(session: Session) -> tuple[VerificationRepository, VerificationEngine, RecoveryEngine]:
    repo = VerificationRepository(session)
    verif_engine = VerificationEngine(repository=repo)
    rec_engine = RecoveryEngine(repository=repo)
    return repo, verif_engine, rec_engine


@router.post("/outcomes", status_code=status.HTTP_201_CREATED)
async def define_expected_outcome(
    payload: ExpectedOutcomeCreateSchema,
    db: Any = Depends(get_db),
) -> dict[str, str]:
    def operation(session: Session) -> dict[str, str]:
        _, verif_engine, _ = _services(session)
        rules = [
            VerificationRule(
                rule_id=r.rule_id,
                rule_type=VerificationType(r.rule_type),
                name=r.name,
                description=r.description,
                target=r.target,
                expected_condition=r.expected_condition,
                severity=RuleSeverity(r.severity),
                retryable=r.retryable,
                requires_human=r.requires_human,
                min_trust_level=EvidenceTrustLevel(r.min_trust_level),
            )
            for r in payload.rules
        ]
        outcome = verif_engine.define_expected_outcome(
            task_id=payload.task_id,
            description=payload.description,
            criteria=payload.criteria,
            rules=rules,
            required_evidence_types=payload.required_evidence_types,
            policy=payload.policy,
        )
        return {"outcome_id": outcome.outcome_id, "task_id": outcome.task_id, "status": "CREATED"}

    return await run_with_sync_session(db, operation)


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
async def register_evidence(
    payload: VerificationEvidenceCreateSchema,
    db: Any = Depends(get_db),
) -> dict[str, str]:
    def operation(session: Session) -> dict[str, str]:
        _, verif_engine, _ = _services(session)
        evidence = verif_engine.add_evidence(
            source_type=payload.source_type,
            source_id=payload.source_id,
            task_id=payload.task_id,
            workspace_id=payload.workspace_id,
            trust_level=EvidenceTrustLevel(payload.trust_level),
            checksum=payload.checksum,
            commit_sha=payload.commit_sha,
            artifact_version=payload.artifact_version,
            payload=payload.payload,
        )
        return {"evidence_id": evidence.evidence_id, "status": "REGISTERED"}

    return await run_with_sync_session(db, operation)


@router.post("/verify", response_model=VerificationResponseSchema)
async def verify_task(
    payload: VerifyTaskRequestSchema,
    db: Any = Depends(get_db),
) -> VerificationResponseSchema:
    def operation(session: Session) -> VerificationResponseSchema:
        _, verif_engine, rec_engine = _services(session)
        result = verif_engine.verify_task(task_id=payload.task_id, evidence_ids=payload.evidence_ids)

        if not result.is_verified:
            # Trigger recovery
            rec_engine.process_verification_failure(result)

        return VerificationResponseSchema(
            verification_id=result.verification_id,
            task_id=result.task_id,
            outcome_id=result.outcome_id,
            status=result.status.value if hasattr(result.status, "value") else str(result.status),
            summary=result.summary,
            recommended_recovery=result.recommended_recovery,
            is_human_verified=result.is_human_verified,
            verified_by_actor_id=result.verified_by_actor_id,
            override_reason=result.override_reason,
            evidence_ids=result.evidence_ids,
        )

    return await run_with_sync_session(db, operation)


@router.get("/{verification_id}", response_model=VerificationResponseSchema)
async def get_verification(
    verification_id: str,
    db: Any = Depends(get_db),
) -> VerificationResponseSchema:
    def operation(session: Session) -> VerificationResponseSchema:
        repo, _, _ = _services(session)
        v = repo.get_verification(verification_id)
        if not v:
            raise HTTPException(status_code=404, detail=f"Verification {verification_id} not found")
        return VerificationResponseSchema(
            verification_id=v.id,
            task_id=v.task_id,
            outcome_id=v.outcome_id,
            status=v.status,
            summary=v.summary,
            recommended_recovery=v.recommended_recovery,
            is_human_verified=v.is_human_verified,
            verified_by_actor_id=v.verified_by_actor_id,
            override_reason=v.override_reason,
            evidence_ids=v.evidence_ids or [],
        )

    return await run_with_sync_session(db, operation)


@router.post("/{verification_id}/override", response_model=VerificationResponseSchema)
async def override_verification(
    verification_id: str,
    payload: HumanOverrideRequestSchema,
    db: Any = Depends(get_db),
) -> VerificationResponseSchema:
    def operation(session: Session) -> VerificationResponseSchema:
        _, verif_engine, _ = _services(session)
        try:
            result = verif_engine.override_verification(
                verification_id=verification_id,
                actor_id=payload.actor_id,
                reason=payload.reason,
                waive=payload.waive,
            )
            return VerificationResponseSchema(
                verification_id=result.verification_id,
                task_id=result.task_id,
                outcome_id=result.outcome_id,
                status=result.status.value if hasattr(result.status, "value") else str(result.status),
                summary=result.summary,
                recommended_recovery=result.recommended_recovery,
                is_human_verified=result.is_human_verified,
                verified_by_actor_id=result.verified_by_actor_id,
                override_reason=result.override_reason,
                evidence_ids=result.evidence_ids,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return await run_with_sync_session(db, operation)
