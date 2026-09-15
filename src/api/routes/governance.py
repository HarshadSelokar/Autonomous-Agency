"""
FastAPI Routes for Phase 11 Human Governance.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas.governance import (
    EmergencyStopRequestSchema,
    GovernanceApprovalDecisionSchema,
    GovernanceApprovalRequestCreateSchema,
    GovernanceApprovalResponseSchema,
    GovernanceOverrideRequestSchema,
    GovernancePolicyCreateSchema,
    HumanInterventionRequestSchema,
    PolicyViolationResponseSchema,
)
from src.application.governance_service import GovernanceService
from src.domain.governance import (
    AutonomyLevel,
    GovernanceRule,
    GovernanceScope,
    RiskLevel,
    ViolationCategory,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.governance_repository import GovernanceRepository

router = APIRouter(prefix="/governance", tags=["Human Governance"])


def get_governance_service(db: Session = Depends(get_db)) -> GovernanceService:
    repo = GovernanceRepository(db)
    return GovernanceService(repository=repo)


@router.post("/policies", status_code=status.HTTP_201_CREATED)
def define_policy(
    payload: GovernancePolicyCreateSchema,
    service: GovernanceService = Depends(get_governance_service),
) -> dict[str, str]:
    rules = [
        GovernanceRule(
            rule_id=r.rule_id,
            name=r.name,
            description=r.description,
            scope=GovernanceScope(r.scope),
            target_pattern=r.target_pattern,
            min_risk_level=RiskLevel(r.min_risk_level),
            autonomy_level=AutonomyLevel(r.autonomy_level),
            required_approver_roles=r.required_approver_roles,
            prohibit_self_approval=r.prohibit_self_approval,
            approval_validity_seconds=r.approval_validity_seconds,
            allow_override=r.allow_override,
        )
        for r in payload.rules
    ]
    policy = service.define_policy(
        name=payload.name,
        scope=GovernanceScope(payload.scope),
        scope_id=payload.scope_id,
        level=payload.level,
        rules=rules,
    )
    return {"policy_id": policy.policy_id, "status": "CREATED"}


@router.post("/approvals", status_code=status.HTTP_201_CREATED, response_model=GovernanceApprovalResponseSchema)
def request_approval(
    payload: GovernanceApprovalRequestCreateSchema,
    service: GovernanceService = Depends(get_governance_service),
) -> GovernanceApprovalResponseSchema:
    req = service.request_approval(
        action_type=payload.action_type,
        action_target=payload.action_target,
        requested_by_actor_id=payload.requested_by_actor_id,
        task_id=payload.task_id,
        project_id=payload.project_id,
        risk_level=RiskLevel(payload.risk_level),
        required_approver_roles=payload.required_approver_roles,
        prohibit_self_approval=payload.prohibit_self_approval,
        validity_seconds=payload.validity_seconds,
        payload=payload.payload,
    )
    return GovernanceApprovalResponseSchema(
        request_id=req.request_id,
        action_type=req.action_type,
        action_target=req.action_target,
        requested_by_actor_id=req.requested_by_actor_id,
        task_id=req.task_id,
        risk_level=req.risk_level.value if hasattr(req.risk_level, "value") else str(req.risk_level),
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        approved_by_actor_id=req.approved_by_actor_id,
        rejection_reason=req.rejection_reason,
        expires_at=str(req.expires_at) if req.expires_at else None,
        created_at=str(req.created_at),
    )


@router.post("/approvals/{request_id}/approve", response_model=GovernanceApprovalResponseSchema)
def approve_request(
    request_id: str,
    payload: GovernanceApprovalDecisionSchema,
    service: GovernanceService = Depends(get_governance_service),
) -> GovernanceApprovalResponseSchema:
    try:
        req = service.approve_request(request_id=request_id, approver_actor_id=payload.actor_id)
        return GovernanceApprovalResponseSchema(
            request_id=req.request_id,
            action_type=req.action_type,
            action_target=req.action_target,
            requested_by_actor_id=req.requested_by_actor_id,
            task_id=req.task_id,
            risk_level=req.risk_level.value if hasattr(req.risk_level, "value") else str(req.risk_level),
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
            approved_by_actor_id=req.approved_by_actor_id,
            rejection_reason=req.rejection_reason,
            expires_at=str(req.expires_at) if req.expires_at else None,
            created_at=str(req.created_at),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/{request_id}/reject", response_model=GovernanceApprovalResponseSchema)
def reject_request(
    request_id: str,
    payload: GovernanceApprovalDecisionSchema,
    service: GovernanceService = Depends(get_governance_service),
) -> GovernanceApprovalResponseSchema:
    try:
        req = service.reject_request(request_id=request_id, rejector_actor_id=payload.actor_id, reason=payload.reason or "Rejected")
        return GovernanceApprovalResponseSchema(
            request_id=req.request_id,
            action_type=req.action_type,
            action_target=req.action_target,
            requested_by_actor_id=req.requested_by_actor_id,
            task_id=req.task_id,
            risk_level=req.risk_level.value if hasattr(req.risk_level, "value") else str(req.risk_level),
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
            approved_by_actor_id=req.approved_by_actor_id,
            rejection_reason=req.rejection_reason,
            expires_at=str(req.expires_at) if req.expires_at else None,
            created_at=str(req.created_at),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop", status_code=status.HTTP_200_OK)
def emergency_stop(
    payload: EmergencyStopRequestSchema,
    service: GovernanceService = Depends(get_governance_service),
) -> dict[str, str]:
    stop = service.activate_emergency_stop(
        activated_by_actor_id=payload.activated_by_actor_id,
        reason=payload.reason,
        scope=GovernanceScope(payload.scope),
        scope_id=payload.scope_id,
    )
    return {"stop_id": stop.stop_id, "status": "ACTIVATED"}


@router.post("/interventions", status_code=status.HTTP_201_CREATED)
def record_intervention(
    payload: HumanInterventionRequestSchema,
    service: GovernanceService = Depends(get_governance_service),
) -> dict[str, str]:
    intv = service.record_human_intervention(
        intervention_type=payload.intervention_type,
        scope=GovernanceScope(payload.scope),
        scope_id=payload.scope_id,
        actor_id=payload.actor_id,
        reason=payload.reason,
        details=payload.details,
    )
    return {"intervention_id": intv.intervention_id, "status": "RECORDED"}


@router.get("/violations", response_model=List[PolicyViolationResponseSchema])
def list_violations(
    service: GovernanceService = Depends(get_governance_service),
) -> List[PolicyViolationResponseSchema]:
    violations_models = service._repository.get_violations()
    return [
        PolicyViolationResponseSchema(
            violation_id=v.id,
            category=v.category,
            summary=v.summary,
            actor_id=v.actor_id,
            task_id=v.task_id,
            severity=v.severity,
            created_at=str(v.created_at),
        )
        for v in violations_models
    ]
