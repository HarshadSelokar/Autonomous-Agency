"""
FastAPI REST API Routes for Phase 28 Autonomous Innovation, New Venture Creation & Governed Expansion.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.infrastructure.repositories.venture_repository import SQLAlchemyVentureRepository
from src.application.innovation_discovery_service import InnovationDiscoveryService
from src.application.venture_business_case_service import VentureBusinessCaseService
from src.application.venture_proposal_service import VentureProposalService
from src.application.venture_lifecycle_service import VentureLifecycleService
from src.domain.venture import VentureType, ProposalStatus
from src.domain.exceptions import (
    UnauthorizedVentureCreationError,
    InvalidVentureLifecycleError,
    VentureLaunchBlockedError,
    CrossCompanyVentureAccessError,
)

router = APIRouter(prefix="/api/v1/ventures", tags=["Autonomous Innovation & Venture Creation"])


# Request Schemas
class CreateOpportunityRequest(BaseModel):
    title: str
    description: str
    problem_statement: str
    customer_need: str
    source: str = "RESEARCH_SIGNAL"
    market_signal: Optional[Dict[str, Any]] = None
    evidence: Optional[List[str]] = None
    strategic_relevance: float = 0.80


class GenerateIdeaRequest(BaseModel):
    opportunity_id: str
    title: str
    description: str
    proposed_solution: str
    target_customer: str
    value_proposition: str
    differentiator: str
    assumptions: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    required_capabilities: Optional[List[str]] = None


class FormulateHypothesisRequest(BaseModel):
    idea_id: str
    assumption: str
    validation_method: str = "RESEARCH_AND_SIMULATION"
    failure_condition: str = "Willingness to pay below threshold"
    supporting_evidence: Optional[List[str]] = None
    confidence: float = 0.50


class ValidateOpportunityRequest(BaseModel):
    validation_method: str
    evidence_summary: str
    confidence_score: float = 0.85
    unresolved_assumptions: Optional[List[str]] = None


class CreateProductConceptRequest(BaseModel):
    idea_id: str
    name: str
    target_segment: str
    capabilities: List[str]
    value_proposition: str
    pricing_hypothesis: Optional[Dict[str, Any]] = None
    distribution_channel: str = "DIRECT_DIGITAL_SALES"


class CreateBusinessModelConceptRequest(BaseModel):
    idea_id: str
    revenue_model: str = "SUBSCRIPTION"
    pricing_model: Optional[Dict[str, Any]] = None
    acquisition_strategy: str = "INBOUND_CONTENT_MARKETING"
    cost_structure: Optional[Dict[str, Any]] = None
    gross_margin_est: float = 0.75
    operating_model: str = "AUTONOMOUS_SWARM_OPERATIONS"


class ConstructBusinessCaseRequest(BaseModel):
    opportunity_id: str
    title: str
    market_assumptions: Optional[Dict[str, Any]] = None
    financial_model: Optional[Dict[str, Any]] = None
    workforce_reqs: Optional[Dict[str, Any]] = None
    infra_reqs: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    scenarios: Optional[Dict[str, Any]] = None
    expected_roi: float = 0.35


class ProposeVentureRequest(BaseModel):
    opportunity_id: str
    business_case_id: str
    title: str
    venture_type: str = "NEW_COMPANY"
    required_budget_usd: int = 15000000
    required_workforce_count: int = 4
    risk_level: str = "MEDIUM"


class GovernanceApprovalRequest(BaseModel):
    governance_approval_id: str


class RejectProposalRequest(BaseModel):
    reason: str = "Rejected by Human Governance Council"


class InitializeVentureRequest(BaseModel):
    target_structure: str = "NEW_COMPANY"
    departments: Optional[List[str]] = None
    workforce_plan: Optional[Dict[str, Any]] = None
    product_config: Optional[Dict[str, Any]] = None
    financial_setup: Optional[Dict[str, Any]] = None


class AssessLaunchReadinessRequest(BaseModel):
    product_ready: bool = True
    technical_ready: bool = True
    security_ready: bool = True
    financial_ready: bool = True
    governance_ready: bool = True


class EvaluateVentureOutcomeRequest(BaseModel):
    expected_outcomes: Dict[str, Any]
    actual_outcomes: Dict[str, Any]


# Route Handlers
@router.post("/companies/{company_id}/opportunities", status_code=status.HTTP_201_CREATED)
async def discover_opportunity(
    company_id: str,
    payload: CreateOpportunityRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = InnovationDiscoveryService(repo)
    opp = await service.discover_opportunity(
        company_id=company_id,
        title=payload.title,
        description=payload.description,
        problem_statement=payload.problem_statement,
        customer_need=payload.customer_need,
        source=payload.source,
        market_signal=payload.market_signal,
        evidence=payload.evidence,
        strategic_relevance=payload.strategic_relevance,
    )
    return {
        "id": opp.id,
        "company_id": opp.company_id,
        "title": opp.title,
        "status": opp.status.value if hasattr(opp.status, "value") else str(opp.status),
        "confidence": opp.confidence,
    }


@router.get("/companies/{company_id}/opportunities")
async def list_opportunities(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = InnovationDiscoveryService(repo)
    opps = await repo.list_opportunities_for_company(company_id)
    return [
        {
            "id": o.id,
            "company_id": o.company_id,
            "title": o.title,
            "status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "confidence": o.confidence,
            "potential_impact": o.potential_impact,
        }
        for o in opps
    ]


@router.post("/companies/{company_id}/opportunities/{opportunity_id}/validate")
async def validate_opportunity(
    company_id: str,
    opportunity_id: str,
    payload: ValidateOpportunityRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = InnovationDiscoveryService(repo)
    try:
        val = await service.validate_opportunity(
            company_id=company_id,
            opportunity_id=opportunity_id,
            validation_method=payload.validation_method,
            evidence_summary=payload.evidence_summary,
            confidence_score=payload.confidence_score,
            unresolved_assumptions=payload.unresolved_assumptions,
        )
        return {
            "validation_id": val.id,
            "opportunity_id": val.opportunity_id,
            "confidence_score": val.confidence_score,
            "validated_at": val.validated_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/ideas", status_code=status.HTTP_201_CREATED)
async def generate_idea(
    company_id: str,
    payload: GenerateIdeaRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = InnovationDiscoveryService(repo)
    try:
        idea = await service.generate_idea(
            company_id=company_id,
            opportunity_id=payload.opportunity_id,
            title=payload.title,
            description=payload.description,
            proposed_solution=payload.proposed_solution,
            target_customer=payload.target_customer,
            value_proposition=payload.value_proposition,
            differentiator=payload.differentiator,
            assumptions=payload.assumptions,
            dependencies=payload.dependencies,
            risks=payload.risks,
            required_capabilities=payload.required_capabilities,
        )
        return {
            "id": idea.id,
            "opportunity_id": idea.opportunity_id,
            "title": idea.title,
            "value_proposition": idea.value_proposition,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/hypotheses", status_code=status.HTTP_201_CREATED)
async def formulate_hypothesis(
    company_id: str,
    payload: FormulateHypothesisRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = InnovationDiscoveryService(repo)
    try:
        hyp = await service.formulate_hypothesis(
            company_id=company_id,
            idea_id=payload.idea_id,
            assumption=payload.assumption,
            validation_method=payload.validation_method,
            failure_condition=payload.failure_condition,
            supporting_evidence=payload.supporting_evidence,
            confidence=payload.confidence,
        )
        return {
            "id": hyp.id,
            "idea_id": hyp.idea_id,
            "assumption": hyp.assumption,
            "status": hyp.status.value if hasattr(hyp.status, "value") else str(hyp.status),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/business-cases", status_code=status.HTTP_201_CREATED)
async def construct_business_case(
    company_id: str,
    payload: ConstructBusinessCaseRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureBusinessCaseService(repo)
    try:
        bcase = await service.construct_business_case(
            company_id=company_id,
            opportunity_id=payload.opportunity_id,
            title=payload.title,
            market_assumptions=payload.market_assumptions,
            financial_model=payload.financial_model,
            workforce_reqs=payload.workforce_reqs,
            infra_reqs=payload.infra_reqs,
            risk_analysis=payload.risk_analysis,
            scenarios=payload.scenarios,
            expected_roi=payload.expected_roi,
        )
        return {
            "id": bcase.id,
            "opportunity_id": bcase.opportunity_id,
            "title": bcase.title,
            "expected_roi": bcase.expected_roi,
            "scenarios": bcase.scenarios,
            "status": bcase.status.value if hasattr(bcase.status, "value") else str(bcase.status),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/companies/{company_id}/business-cases/{business_case_id}/sensitivity")
async def perform_sensitivity_analysis(
    company_id: str,
    business_case_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureBusinessCaseService(repo)
    try:
        res = await service.perform_sensitivity_analysis(
            business_case_id=business_case_id,
            company_id=company_id,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/proposals", status_code=status.HTTP_201_CREATED)
async def propose_venture(
    company_id: str,
    payload: ProposeVentureRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureProposalService(repo)
    try:
        vtype = VentureType(payload.venture_type)
    except ValueError:
        vtype = VentureType.NEW_COMPANY

    prop = await service.propose_venture(
        company_id=company_id,
        opportunity_id=payload.opportunity_id,
        business_case_id=payload.business_case_id,
        title=payload.title,
        venture_type=vtype,
        required_budget_usd=payload.required_budget_usd,
        required_workforce_count=payload.required_workforce_count,
        risk_level=payload.risk_level,
    )
    return {
        "id": prop.id,
        "opportunity_id": prop.opportunity_id,
        "title": prop.title,
        "venture_type": prop.venture_type.value if hasattr(prop.venture_type, "value") else str(prop.venture_type),
        "status": prop.status.value if hasattr(prop.status, "value") else str(prop.status),
        "governance_required": prop.governance_required,
        "governance_approval_id": prop.governance_approval_id,
    }


@router.get("/companies/{company_id}/proposals")
async def list_proposals(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    props = await repo.list_proposals_for_company(company_id)
    return [
        {
            "id": p.id,
            "company_id": p.company_id,
            "title": p.title,
            "venture_type": p.venture_type.value if hasattr(p.venture_type, "value") else str(p.venture_type),
            "status": p.status.value if hasattr(p.status, "value") else str(p.status),
            "required_budget_usd": p.required_budget_usd,
            "governance_approval_id": p.governance_approval_id,
        }
        for p in props
    ]


@router.post("/companies/{company_id}/proposals/{proposal_id}/approve")
async def attach_governance_approval(
    company_id: str,
    proposal_id: str,
    payload: GovernanceApprovalRequest,
    x_user_id: Optional[str] = Header("GOVERNOR_HUMAN", alias="X-User-ID"),
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureProposalService(repo)
    try:
        prop = await service.attach_governance_approval(
            proposal_id=proposal_id,
            company_id=company_id,
            governance_approval_id=payload.governance_approval_id,
            governor_id=x_user_id or "GOVERNOR_HUMAN",
        )
        return {
            "proposal_id": prop.id,
            "status": prop.status.value if hasattr(prop.status, "value") else str(prop.status),
            "governance_approval_id": prop.governance_approval_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/proposals/{proposal_id}/initialize")
async def initialize_venture(
    company_id: str,
    proposal_id: str,
    payload: InitializeVentureRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureLifecycleService(repo)
    try:
        try:
            target_struct = VentureType(payload.target_structure)
        except ValueError:
            target_struct = VentureType.NEW_COMPANY

        init_res = await service.initialize_venture(
            proposal_id=proposal_id,
            company_id=company_id,
            target_structure=target_struct,
            departments=payload.departments,
            workforce_plan=payload.workforce_plan,
            product_config=payload.product_config,
            financial_setup=payload.financial_setup,
        )
        return init_res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except UnauthorizedVentureCreationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("/companies/{company_id}/proposals/{proposal_id}/launch-readiness")
async def assess_launch_readiness(
    company_id: str,
    proposal_id: str,
    payload: AssessLaunchReadinessRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureLifecycleService(repo)
    readiness = await service.assess_launch_readiness(
        proposal_id=proposal_id,
        company_id=company_id,
        product_ready=payload.product_ready,
        technical_ready=payload.technical_ready,
        security_ready=payload.security_ready,
        financial_ready=payload.financial_ready,
        governance_ready=payload.governance_ready,
    )
    return {
        "readiness_id": readiness.id,
        "proposal_id": readiness.proposal_id,
        "status": readiness.status.value if hasattr(readiness.status, "value") else str(readiness.status),
    }


@router.post("/companies/{company_id}/proposals/{proposal_id}/launch")
async def launch_venture(
    company_id: str,
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureLifecycleService(repo)
    try:
        launch_res = await service.launch_venture(
            proposal_id=proposal_id,
            company_id=company_id,
        )
        return launch_res
    except VentureLaunchBlockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/companies/{company_id}/ventures/{venture_id}/evaluate-outcome")
async def evaluate_venture_outcome(
    company_id: str,
    venture_id: str,
    payload: EvaluateVentureOutcomeRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    service = VentureLifecycleService(repo)
    outcome = await service.evaluate_venture_outcome(
        venture_id=venture_id,
        company_id=company_id,
        expected_outcomes=payload.expected_outcomes,
        actual_outcomes=payload.actual_outcomes,
    )
    return {
        "outcome_id": outcome.id,
        "venture_id": outcome.venture_id,
        "status": outcome.status.value if hasattr(outcome.status, "value") else str(outcome.status),
        "variance_analysis": outcome.variance_analysis,
    }


@router.get("/companies/{company_id}/portfolio")
async def get_portfolio(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyVentureRepository(db)
    opps = await repo.list_opportunities_for_company(company_id)
    props = await repo.list_proposals_for_company(company_id)
    bcases = await repo.list_business_cases_for_company(company_id)

    total_budget = sum(p.required_budget_usd for p in props if p.status == ProposalStatus.APPROVED)

    return {
        "company_id": company_id,
        "opportunities_count": len(opps),
        "business_cases_count": len(bcases),
        "proposals_count": len(props),
        "approved_ventures_count": len([p for p in props if p.status == ProposalStatus.APPROVED]),
        "total_budget_allocated_usd": total_budget,
    }
