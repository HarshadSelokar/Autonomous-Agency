"""
FastAPI Routes for Phase 6 Decision Management.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.decision_schemas import (
    ApproveDecisionRequest,
    CreateDecisionRequest,
    DecisionResponse,
    RejectDecisionRequest,
    SupersedeDecisionRequest,
)
from src.application.decision_authority_service import (
    DecisionAuthorityService,
    UnauthorizedDecisionApprovalError,
)
from src.application.decision_integration_service import DecisionIntegrationService
from src.domain.decision import (
    Decision,
    DecisionProvenance,
    DecisionStatus,
    DecisionType,
)
from src.domain.exceptions import ObjectiveValidationError
from src.infrastructure.database import get_db
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository

router = APIRouter(prefix="/decisions", tags=["Decisions"])


def _to_decision_response(decision: Decision) -> DecisionResponse:
    return DecisionResponse(
        id=decision.id,
        title=decision.title,
        question=decision.question,
        status=decision.status.value,
        decision_maker_employee_id=decision.decision_maker_employee_id,
        decision_type=decision.decision_type.value,
        approving_authority_role=decision.approving_authority_role,
        chosen_option=decision.chosen_option,
        alternatives=decision.alternatives,
        rationale=decision.rationale,
        meeting_id=decision.meeting_id,
        objective_id=decision.objective_id,
        task_id=decision.task_id,
        previous_decision_id=decision.previous_decision_id,
        provenance=decision.provenance.value,
        created_at=decision.created_at,
        approved_at=decision.approved_at,
    )


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    payload: CreateDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> DecisionResponse:
    repo = SQLAlchemyDecisionRepository(db)
    try:
        decision_id = f"dec-{uuid.uuid4().hex[:8]}"
        type_enum = DecisionType(payload.decision_type.upper())
        provenance_enum = DecisionProvenance(payload.provenance.upper())

        decision = Decision(
            id=decision_id,
            title=payload.title,
            question=payload.question,
            decision_maker_employee_id=payload.decision_maker_employee_id,
            description=payload.description,
            status=DecisionStatus.PROPOSED,
            decision_type=type_enum,
            approving_authority_role=payload.approving_authority_role,
            chosen_option=payload.chosen_option,
            alternatives=payload.alternatives,
            rationale=payload.rationale,
            consequences=payload.consequences,
            evidence=payload.evidence,
            meeting_id=payload.meeting_id,
            objective_id=payload.objective_id,
            plan_id=payload.plan_id,
            task_id=payload.task_id,
            provenance=provenance_enum,
        )
        saved = await repo.save(decision)
        await db.commit()
        return _to_decision_response(saved)
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("", response_model=list[DecisionResponse])
async def list_decisions(
    db: AsyncSession = Depends(get_db),
) -> list[DecisionResponse]:
    repo = SQLAlchemyDecisionRepository(db)
    decisions = await repo.list_all()
    return [_to_decision_response(d) for d in decisions]


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
) -> DecisionResponse:
    repo = SQLAlchemyDecisionRepository(db)
    decision = await repo.get_by_id(decision_id)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Decision '{decision_id}' not found.")
    return _to_decision_response(decision)


@router.post("/{decision_id}/approve", response_model=DecisionResponse)
async def approve_decision(
    decision_id: str,
    payload: ApproveDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> DecisionResponse:
    decision_repo = SQLAlchemyDecisionRepository(db)
    employee_repo = SQLAlchemyEmployeeRepository(db)
    auth_service = DecisionAuthorityService(employee_repo=employee_repo)
    integration_service = DecisionIntegrationService(decision_repo=decision_repo)

    decision = await decision_repo.get_by_id(decision_id)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Decision '{decision_id}' not found.")

    try:
        provenance_enum = DecisionProvenance(payload.provenance.upper()) if payload.provenance else None
        approved = await auth_service.approve_decision(
            decision=decision,
            approver_employee_id=payload.approver_employee_id,
            provenance=provenance_enum,
        )
        saved = await decision_repo.save(approved)
        await db.commit()
        await integration_service.execute_approved_decision_actions(
            decision_id=saved.id, actor_employee_id=payload.approver_employee_id
        )
        await db.commit()
        return _to_decision_response(saved)
    except UnauthorizedDecisionApprovalError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{decision_id}/reject", response_model=DecisionResponse)
async def reject_decision(
    decision_id: str,
    payload: RejectDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> DecisionResponse:
    decision_repo = SQLAlchemyDecisionRepository(db)
    employee_repo = SQLAlchemyEmployeeRepository(db)
    auth_service = DecisionAuthorityService(employee_repo=employee_repo)

    decision = await decision_repo.get_by_id(decision_id)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Decision '{decision_id}' not found.")

    try:
        rejected = await auth_service.reject_decision(
            decision=decision,
            approver_employee_id=payload.approver_employee_id,
            reason=payload.reason,
        )
        saved = await decision_repo.save(rejected)
        await db.commit()
        return _to_decision_response(saved)
    except UnauthorizedDecisionApprovalError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{decision_id}/supersede", response_model=DecisionResponse)
async def supersede_decision(
    decision_id: str,
    payload: SupersedeDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> DecisionResponse:
    decision_repo = SQLAlchemyDecisionRepository(db)
    try:
        superseded = await decision_repo.supersede_decision(
            old_decision_id=decision_id,
            new_decision_id=payload.new_decision_id,
            actor_employee_id=payload.actor_employee_id,
        )
        return _to_decision_response(superseded)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
