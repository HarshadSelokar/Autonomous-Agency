"""
Phase 27 Continuous Organizational Learning & Governed Adaptation REST API Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.infrastructure.repositories.learning_repository import SQLAlchemyLearningRepository
from src.application.learning_cycle_service import LearningCycleService
from src.application.outcome_comparison_service import OutcomeComparisonService
from src.application.adaptation_proposal_service import AdaptationProposalService
from src.application.controlled_experiment_service import ControlledExperimentService
from src.application.learning_context_builder import LearningContextBuilder
from src.domain.learning import LearningScope, AdaptationType, AdaptationRiskLevel
from src.domain.exceptions import UnauthorizedAdaptationExecutionError, InvalidAdaptationStateError, AdaptationRollbackError

router = APIRouter(prefix="/api/v1/learning", tags=["Continuous Organizational Learning & Adaptation"])


# Request / Response Schemas
class StartLearningCycleRequest(BaseModel):
    purpose: str
    scope: LearningScope = LearningScope.COMPANY
    simulation_id: Optional[str] = None


class IngestObservationRequest(BaseModel):
    cycle_id: str
    source_subsystem: str
    entity_reference: str
    observed_value: Any
    expected_value: Any = None
    context_data: Optional[Dict[str, Any]] = None


class CompareExpectedVsActualRequest(BaseModel):
    cycle_id: str
    domain: str
    metric_name: str
    expected_value: float
    actual_value: float
    context: Optional[Dict[str, Any]] = None


class GenerateCandidateRequest(BaseModel):
    cycle_id: str
    statement: str
    scope: LearningScope = LearningScope.COMPANY
    supporting_observation_ids: Optional[List[str]] = None
    assumptions: Optional[List[str]] = None


class ValidateCandidateRequest(BaseModel):
    validation_method: str = "HISTORICAL_ANALYSIS"
    is_valid: bool = True
    evidence_score: float = 0.85
    validation_notes: str = ""


class CreateOpportunityRequest(BaseModel):
    title: str
    affected_area: str
    expected_impact: str
    required_resources: Optional[Dict[str, Any]] = None
    risks: Optional[List[str]] = None
    constraints: Optional[List[str]] = None


class ProposeAdaptationRequest(BaseModel):
    opportunity_id: str
    adaptation_type: AdaptationType = AdaptationType.WORKFLOW_CHANGE
    risk_level: AdaptationRiskLevel = AdaptationRiskLevel.MEDIUM
    current_state: Optional[Dict[str, Any]] = None
    proposed_state: Optional[Dict[str, Any]] = None
    rationale: str = ""
    rollback_plan: Optional[Dict[str, Any]] = None


class ApproveAdaptationRequest(BaseModel):
    governance_approval_id: str


class DispatchExperimentRequest(BaseModel):
    governance_approval_id: str
    target_subsystem: str = "WORKFLOW_ENGINE"


class EvaluateExperimentOutcomeRequest(BaseModel):
    execution_id: str
    expected_metrics: Dict[str, Any]
    actual_metrics: Dict[str, Any]
    side_effects_detected: Optional[List[str]] = None


class RollbackAdaptationRequest(BaseModel):
    reason: str = "Regression detected during evaluation."


# Route Handlers
@router.post("/companies/{company_id}/cycles", status_code=status.HTTP_201_CREATED)
async def start_learning_cycle(
    company_id: str,
    payload: StartLearningCycleRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = LearningCycleService(repo)
    cycle = await service.start_learning_cycle(
        company_id=company_id,
        purpose=payload.purpose,
        scope=payload.scope,
        simulation_id=payload.simulation_id,
    )
    return {
        "id": cycle.id,
        "company_id": cycle.company_id,
        "purpose": cycle.purpose,
        "status": cycle.status.value,
        "created_at": cycle.created_at.isoformat(),
    }


@router.get("/companies/{company_id}/cycles/{cycle_id}")
async def get_learning_cycle(
    company_id: str,
    cycle_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    cycle = await repo.get_learning_cycle_by_id(cycle_id)
    if not cycle or cycle.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning cycle not found.")
    return {
        "id": cycle.id,
        "company_id": cycle.company_id,
        "purpose": cycle.purpose,
        "scope": cycle.scope.value,
        "status": cycle.status.value,
        "observations_count": cycle.observations_count,
        "patterns_count": cycle.patterns_count,
        "candidates_count": cycle.candidates_count,
        "created_at": cycle.created_at.isoformat(),
    }


@router.get("/companies/{company_id}/cycles")
async def list_learning_cycles(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    cycles = await repo.list_learning_cycles_for_company(company_id)
    return [
        {
            "id": c.id,
            "purpose": c.purpose,
            "status": c.status.value,
            "observations_count": c.observations_count,
            "created_at": c.created_at.isoformat(),
        }
        for c in cycles
    ]


@router.post("/companies/{company_id}/observations", status_code=status.HTTP_201_CREATED)
async def ingest_observation(
    company_id: str,
    payload: IngestObservationRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = LearningCycleService(repo)
    try:
        obs = await service.ingest_observation(
            cycle_id=payload.cycle_id,
            company_id=company_id,
            source_subsystem=payload.source_subsystem,
            entity_reference=payload.entity_reference,
            observed_value=payload.observed_value,
            expected_value=payload.expected_value,
            context_data=payload.context_data,
        )
        return {"id": obs.id, "cycle_id": obs.cycle_id, "source_subsystem": obs.source_subsystem}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/comparisons", status_code=status.HTTP_201_CREATED)
async def compare_expected_vs_actual(
    company_id: str,
    payload: CompareExpectedVsActualRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = OutcomeComparisonService(repo)
    comp = await service.compare_expected_vs_actual(
        cycle_id=payload.cycle_id,
        company_id=company_id,
        domain=payload.domain,
        metric_name=payload.metric_name,
        expected_value=payload.expected_value,
        actual_value=payload.actual_value,
        context=payload.context,
    )
    return {
        "id": comp.id,
        "domain": comp.domain,
        "metric_name": comp.metric_name,
        "variance": comp.variance,
        "variance_percentage": comp.variance_percentage,
    }


@router.post("/companies/{company_id}/candidates", status_code=status.HTTP_201_CREATED)
async def generate_learning_candidate(
    company_id: str,
    payload: GenerateCandidateRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = LearningCycleService(repo)
    try:
        candidate = await service.generate_learning_candidate(
            cycle_id=payload.cycle_id,
            company_id=company_id,
            statement=payload.statement,
            scope=payload.scope,
            supporting_observation_ids=payload.supporting_observation_ids,
            assumptions=payload.assumptions,
        )
        return {
            "id": candidate.id,
            "statement": candidate.statement,
            "confidence": candidate.confidence,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/candidates/{candidate_id}/validate")
async def validate_candidate(
    company_id: str,
    candidate_id: str,
    payload: ValidateCandidateRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = LearningCycleService(repo)
    try:
        val = await service.validate_candidate(
            candidate_id=candidate_id,
            company_id=company_id,
            validation_method=payload.validation_method,
            is_valid=payload.is_valid,
            evidence_score=payload.evidence_score,
            validation_notes=payload.validation_notes,
        )
        return {
            "validation_id": val.id,
            "candidate_id": val.candidate_id,
            "is_valid": val.is_valid,
            "evidence_score": val.evidence_score,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/companies/{company_id}/lessons")
async def list_validated_lessons(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    candidates = await repo.list_learning_candidates_for_company(company_id)
    return [
        {
            "id": c.id,
            "statement": c.statement,
            "scope": c.scope.value,
            "confidence": c.confidence,
            "created_at": c.created_at.isoformat(),
        }
        for c in candidates
        if c.confidence >= 0.70
    ]


@router.get("/companies/{company_id}/patterns")
async def list_learning_patterns(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    patterns = await repo.list_learning_patterns_for_company(company_id)
    return [
        {
            "id": p.id,
            "pattern_name": p.pattern_name,
            "pattern_type": p.pattern_type,
            "frequency": p.frequency,
            "confidence": p.confidence,
        }
        for p in patterns
    ]


@router.post("/companies/{company_id}/improvements", status_code=status.HTTP_201_CREATED)
async def create_improvement_opportunity(
    company_id: str,
    payload: CreateOpportunityRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = AdaptationProposalService(repo)
    opp = await service.identify_improvement_opportunity(
        company_id=company_id,
        title=payload.title,
        affected_area=payload.affected_area,
        expected_impact=payload.expected_impact,
        required_resources=payload.required_resources,
        risks=payload.risks,
        constraints=payload.constraints,
    )
    return {"id": opp.id, "title": opp.title, "affected_area": opp.affected_area}


@router.get("/companies/{company_id}/improvements")
async def list_improvement_opportunities(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    opps = await repo.list_improvement_opportunities_for_company(company_id)
    return [
        {
            "id": o.id,
            "title": o.title,
            "affected_area": o.affected_area,
            "expected_impact": o.expected_impact,
            "confidence": o.confidence,
        }
        for o in opps
    ]


@router.post("/companies/{company_id}/adaptations", status_code=status.HTTP_201_CREATED)
async def propose_adaptation(
    company_id: str,
    payload: ProposeAdaptationRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = AdaptationProposalService(repo)
    proposal = await service.propose_adaptation(
        company_id=company_id,
        opportunity_id=payload.opportunity_id,
        adaptation_type=payload.adaptation_type,
        risk_level=payload.risk_level,
        current_state=payload.current_state,
        proposed_state=payload.proposed_state,
        rationale=payload.rationale,
        rollback_plan=payload.rollback_plan,
    )
    return {
        "id": proposal.id,
        "opportunity_id": proposal.opportunity_id,
        "adaptation_type": proposal.adaptation_type.value,
        "risk_level": proposal.risk_level.value,
        "status": proposal.status.value,
        "governance_required": proposal.governance_required,
    }


@router.get("/companies/{company_id}/adaptations/{adaptation_id}")
async def get_adaptation_proposal(
    company_id: str,
    adaptation_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    proposal = await repo.get_adaptation_proposal_by_id(adaptation_id)
    if not proposal or proposal.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adaptation proposal not found.")
    return {
        "id": proposal.id,
        "opportunity_id": proposal.opportunity_id,
        "adaptation_type": proposal.adaptation_type.value,
        "risk_level": proposal.risk_level.value,
        "rationale": proposal.rationale,
        "status": proposal.status.value,
        "governance_required": proposal.governance_required,
        "governance_approval_id": proposal.governance_approval_id,
    }


@router.post("/companies/{company_id}/adaptations/{adaptation_id}/approve")
async def approve_adaptation(
    company_id: str,
    adaptation_id: str,
    payload: ApproveAdaptationRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = AdaptationProposalService(repo)
    try:
        proposal = await service.attach_governance_approval(
            proposal_id=adaptation_id,
            company_id=company_id,
            governance_approval_id=payload.governance_approval_id,
        )
        return {
            "id": proposal.id,
            "status": proposal.status.value,
            "governance_approval_id": proposal.governance_approval_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/adaptations/{adaptation_id}/experiment")
async def dispatch_experiment(
    company_id: str,
    adaptation_id: str,
    payload: DispatchExperimentRequest,
    x_user_id: Optional[str] = Header("SYSTEM", alias="X-User-ID"),
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = ControlledExperimentService(repo)
    try:
        execution = await service.dispatch_experiment(
            proposal_id=adaptation_id,
            company_id=company_id,
            actor_id=x_user_id or "SYSTEM",
            governance_approval_id=payload.governance_approval_id,
            target_subsystem=payload.target_subsystem,
        )
        return {
            "execution_id": execution.id,
            "proposal_id": execution.proposal_id,
            "execution_type": execution.execution_type,
            "governance_approval_id": execution.governance_approval_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except UnauthorizedAdaptationExecutionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except InvalidAdaptationStateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/companies/{company_id}/adaptations/{adaptation_id}/evaluate-outcome")
async def evaluate_experiment_outcome(
    company_id: str,
    adaptation_id: str,
    payload: EvaluateExperimentOutcomeRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = ControlledExperimentService(repo)
    try:
        outcome = await service.evaluate_experiment_outcome(
            execution_id=payload.execution_id,
            company_id=company_id,
            expected_metrics=payload.expected_metrics,
            actual_metrics=payload.actual_metrics,
            side_effects_detected=payload.side_effects_detected,
        )
        return {
            "outcome_id": outcome.id,
            "proposal_id": outcome.proposal_id,
            "has_regression": outcome.has_regression,
            "variance_analysis": outcome.variance_analysis,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/adaptations/{adaptation_id}/adopt")
async def adopt_adaptation(
    company_id: str,
    adaptation_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = ControlledExperimentService(repo)
    try:
        proposal = await service.adopt_adaptation(proposal_id=adaptation_id, company_id=company_id)
        return {"id": proposal.id, "status": proposal.status.value}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/companies/{company_id}/adaptations/{adaptation_id}/rollback")
async def rollback_adaptation(
    company_id: str,
    adaptation_id: str,
    payload: RollbackAdaptationRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    service = ControlledExperimentService(repo)
    try:
        proposal = await service.rollback_adaptation(
            proposal_id=adaptation_id, company_id=company_id, reason=payload.reason
        )
        return {"id": proposal.id, "status": proposal.status.value}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AdaptationRollbackError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/companies/{company_id}/context")
async def get_learning_context(
    company_id: str,
    max_lessons: int = 5,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyLearningRepository(db)
    builder = LearningContextBuilder(repo)
    context_text = await builder.build_learning_context(company_id=company_id, max_lessons=max_lessons)
    return {"company_id": company_id, "learning_context": context_text}
