"""
FastAPI Routes for Phase 11 Human Governance.

The governance repository is written against the synchronous Session API, so each route
runs its work through run_with_sync_session on the request's AsyncSession.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.schemas.governance import (
    EmergencyStopRequestSchema,
    GovernanceApprovalDecisionSchema,
    GovernanceApprovalRequestCreateSchema,
    GovernanceApprovalResponseSchema,
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
)
from src.infrastructure.database import get_db, run_with_sync_session
from src.infrastructure.models.governance_model import GovernanceApprovalRequestModel
from src.infrastructure.repositories.governance_repository import GovernanceRepository

router = APIRouter(prefix="/governance", tags=["Human Governance"])


def _service(session: Session) -> GovernanceService:
    return GovernanceService(repository=GovernanceRepository(session))


def _approval_response(req: Any) -> GovernanceApprovalResponseSchema:
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


@router.post("/policies", status_code=status.HTTP_201_CREATED)
async def define_policy(
    payload: GovernancePolicyCreateSchema,
    db: Any = Depends(get_db),
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

    def operation(session: Session) -> dict[str, str]:
        policy = _service(session).define_policy(
            name=payload.name,
            scope=GovernanceScope(payload.scope),
            scope_id=payload.scope_id,
            level=payload.level,
            rules=rules,
        )
        return {"policy_id": policy.policy_id, "status": "CREATED"}

    return await run_with_sync_session(db, operation)


@router.post("/approvals", status_code=status.HTTP_201_CREATED, response_model=GovernanceApprovalResponseSchema)
async def request_approval(
    payload: GovernanceApprovalRequestCreateSchema,
    db: Any = Depends(get_db),
) -> GovernanceApprovalResponseSchema:
    def operation(session: Session) -> GovernanceApprovalResponseSchema:
        req = _service(session).request_approval(
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
        return _approval_response(req)

    return await run_with_sync_session(db, operation)


@router.get("/approvals", response_model=List[GovernanceApprovalResponseSchema])
async def list_approval_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Any = Depends(get_db),
) -> List[GovernanceApprovalResponseSchema]:
    def operation(session: Session) -> List[GovernanceApprovalResponseSchema]:
        stmt = select(GovernanceApprovalRequestModel)
        if status_filter:
            stmt = stmt.where(GovernanceApprovalRequestModel.status == status_filter.upper())
        return [
            GovernanceApprovalResponseSchema(
                request_id=req.id,
                action_type=req.action_type,
                action_target=req.action_target,
                requested_by_actor_id=req.requested_by_actor_id,
                task_id=req.task_id,
                risk_level=str(req.risk_level),
                status=str(req.status),
                approved_by_actor_id=req.approved_by_actor_id,
                rejection_reason=req.rejection_reason,
                expires_at=str(req.expires_at) if req.expires_at else None,
                created_at=str(req.created_at),
            )
            for req in session.execute(stmt).scalars().all()
        ]

    return await run_with_sync_session(db, operation)


@router.post("/approvals/{request_id}/approve", response_model=GovernanceApprovalResponseSchema)
async def approve_request(
    request_id: str,
    payload: GovernanceApprovalDecisionSchema,
    db: Any = Depends(get_db),
) -> GovernanceApprovalResponseSchema:
    def operation(session: Session) -> GovernanceApprovalResponseSchema:
        req = _service(session).approve_request(
            request_id=request_id, approver_actor_id=payload.actor_id
        )
        return _approval_response(req)

    try:
        return await run_with_sync_session(db, operation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/{request_id}/reject", response_model=GovernanceApprovalResponseSchema)
async def reject_request(
    request_id: str,
    payload: GovernanceApprovalDecisionSchema,
    db: Any = Depends(get_db),
) -> GovernanceApprovalResponseSchema:
    def operation(session: Session) -> GovernanceApprovalResponseSchema:
        req = _service(session).reject_request(
            request_id=request_id,
            rejector_actor_id=payload.actor_id,
            reason=payload.reason or "Rejected",
        )
        return _approval_response(req)

    try:
        return await run_with_sync_session(db, operation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop", status_code=status.HTTP_200_OK)
async def emergency_stop(
    payload: EmergencyStopRequestSchema,
    db: Any = Depends(get_db),
) -> dict[str, str]:
    def operation(session: Session) -> dict[str, str]:
        stop = _service(session).activate_emergency_stop(
            activated_by_actor_id=payload.activated_by_actor_id,
            reason=payload.reason,
            scope=GovernanceScope(payload.scope),
            scope_id=payload.scope_id,
        )
        return {"stop_id": stop.stop_id, "status": "ACTIVATED"}

    return await run_with_sync_session(db, operation)


@router.post("/interventions", status_code=status.HTTP_201_CREATED)
async def record_intervention(
    payload: HumanInterventionRequestSchema,
    db: Any = Depends(get_db),
) -> dict[str, str]:
    def operation(session: Session) -> dict[str, str]:
        intv = _service(session).record_human_intervention(
            intervention_type=payload.intervention_type,
            scope=GovernanceScope(payload.scope),
            scope_id=payload.scope_id,
            actor_id=payload.actor_id,
            reason=payload.reason,
            details=payload.details,
        )
        return {"intervention_id": intv.intervention_id, "status": "RECORDED"}

    return await run_with_sync_session(db, operation)


@router.get("/violations", response_model=List[PolicyViolationResponseSchema])
async def list_violations(
    db: Any = Depends(get_db),
) -> List[PolicyViolationResponseSchema]:
    def operation(session: Session) -> List[PolicyViolationResponseSchema]:
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
            for v in GovernanceRepository(session).get_violations()
        ]

    return await run_with_sync_session(db, operation)
