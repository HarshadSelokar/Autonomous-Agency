"""FastAPI Routes for Phase 19 Innovation Engine & Strategic Opportunity Services."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.research import (
    ApproveProposalRequest,
    CreateInnovationProposalRequest,
    IdentifyOpportunityRequest,
    InnovationProposalResponse,
)
from src.application.research_services import InnovationEngineService
from src.domain.research import (
    InnovationProposal,
    InnovationType,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.research_repository import SQLAlchemyResearchRepository

router = APIRouter(prefix="/innovation", tags=["Innovation Engine"])


def _to_proposal_response(prop: InnovationProposal) -> InnovationProposalResponse:
    return InnovationProposalResponse(
        id=prop.id,
        opportunity_id=prop.opportunity_id,
        title=prop.title,
        innovation_type=prop.innovation_type.value if hasattr(prop.innovation_type, "value") else str(prop.innovation_type),
        problem_statement=prop.problem_statement,
        evidence_ids=prop.evidence_ids,
        proposed_solution=prop.proposed_solution,
        expected_value=prop.expected_value,
        reversibility=prop.reversibility,
        governance_request_id=prop.governance_request_id,
        is_approved=prop.is_approved,
        strategic_initiative_id=prop.strategic_initiative_id,
        created_at=prop.created_at,
    )


@router.post("/opportunities", status_code=status.HTTP_201_CREATED)
async def identify_opportunity(
    payload: IdentifyOpportunityRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    svc = InnovationEngineService(repo)
    opp = await svc.identify_opportunity(
        finding_id=payload.finding_id,
        title=payload.title,
        description=payload.description,
        estimated_value_score=payload.estimated_value_score,
    )
    await db.commit()
    return {
        "id": opp.id,
        "finding_id": opp.finding_id,
        "title": opp.title,
        "status": opp.status.value if hasattr(opp.status, "value") else str(opp.status),
        "estimated_value_score": opp.estimated_value_score,
    }


@router.post("/proposals", response_model=InnovationProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_innovation_proposal(
    payload: CreateInnovationProposalRequest,
    db: AsyncSession = Depends(get_db),
) -> InnovationProposalResponse:
    repo = SQLAlchemyResearchRepository(db)
    svc = InnovationEngineService(repo)
    try:
        itype = InnovationType(payload.innovation_type.upper())
    except ValueError:
        itype = InnovationType.PRODUCT_INNOVATION

    try:
        prop = await svc.create_innovation_proposal(
            opportunity_id=payload.opportunity_id,
            title=payload.title,
            innovation_type=itype,
            problem_statement=payload.problem_statement,
            proposed_solution=payload.proposed_solution,
            expected_value=payload.expected_value,
            evidence_ids=payload.evidence_ids,
            reversibility=payload.reversibility,
        )
        await db.commit()
        return _to_proposal_response(prop)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get("/proposals", response_model=list[InnovationProposalResponse])
async def list_innovation_proposals(
    db: AsyncSession = Depends(get_db),
) -> list[InnovationProposalResponse]:
    repo = SQLAlchemyResearchRepository(db)
    proposals = await repo.list_proposals()
    return [_to_proposal_response(p) for p in proposals]


@router.post("/proposals/{proposal_id}/approve", response_model=InnovationProposalResponse, status_code=status.HTTP_200_OK)
async def approve_proposal_by_governance(
    proposal_id: str,
    payload: ApproveProposalRequest,
    db: AsyncSession = Depends(get_db),
) -> InnovationProposalResponse:
    repo = SQLAlchemyResearchRepository(db)
    svc = InnovationEngineService(repo)
    try:
        approved_prop = await svc.approve_proposal_by_governance(
            proposal_id=proposal_id,
            governance_request_id=payload.governance_request_id,
        )
        await db.commit()
        return _to_proposal_response(approved_prop)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
