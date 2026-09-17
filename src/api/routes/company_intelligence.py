"""
Phase 26 Company Intelligence & Decision Support REST API Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.infrastructure.repositories.company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
from src.application.company_intelligence_service import CompanyIntelligenceService
from src.application.decision_support_service import DecisionSupportService
from src.application.decision_execution_bridge_service import DecisionExecutionBridgeService
from src.application.decision_outcome_learning_service import DecisionOutcomeLearningService
from src.domain.company_intelligence import QuestionUrgency
from src.domain.exceptions import UnauthorizedDecisionExecutionError, DecisionInsightExpiredError

router = APIRouter(prefix="/api/v1/intelligence", tags=["Company Intelligence & Decision Support"])


# Request / Response Schemas
class StartIntelligenceRunRequest(BaseModel):
    purpose: str
    scope: str = "FULL_COMPANY"
    data_sources: Optional[List[str]] = None


class DecisionQuestionCreateRequest(BaseModel):
    question: str
    purpose: str
    scope: str = "STRATEGIC"
    urgency: QuestionUrgency = QuestionUrgency.MEDIUM
    constraints: Optional[List[str]] = None


class EvaluateOptionsRequest(BaseModel):
    options_data: List[Dict[str, Any]]


class ExecuteInsightRequest(BaseModel):
    governance_approval_id: str


class EvaluateOutcomeRequest(BaseModel):
    insight_id: str
    executed_option_id: str
    expected_outcomes: Dict[str, Any]
    actual_outcomes: Dict[str, Any]


# Route Handlers
@router.post("/companies/{company_id}/runs", status_code=status.HTTP_201_CREATED)
async def start_intelligence_run(
    company_id: str,
    payload: StartIntelligenceRunRequest,
    x_user_id: Optional[str] = Header("SYSTEM", alias="X-User-ID"),
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    service = CompanyIntelligenceService(repo)
    run = await service.start_intelligence_run(
        company_id=company_id,
        purpose=payload.purpose,
        scope=payload.scope,
        requesting_principal=x_user_id or "SYSTEM",
        data_sources=payload.data_sources,
    )
    executed = await service.execute_intelligence_run(run.id)
    return {
        "id": executed.id,
        "company_id": executed.company_id,
        "status": executed.status.value,
        "findings_count": executed.findings_count,
        "uncertainty_score": executed.uncertainty_score,
    }


@router.get("/companies/{company_id}/runs")
async def list_intelligence_runs(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    service = CompanyIntelligenceService(repo)
    runs = await repo.list_intelligence_runs_for_company(company_id)
    return [
        {
            "id": r.id,
            "purpose": r.purpose,
            "status": r.status.value,
            "findings_count": r.findings_count,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]


@router.get("/companies/{company_id}/runs/{run_id}")
async def get_intelligence_run(
    company_id: str,
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    run = await repo.get_intelligence_run_by_id(run_id)
    if not run or run.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intelligence run not found.")
    return {
        "id": run.id,
        "company_id": run.company_id,
        "purpose": run.purpose,
        "scope": run.scope,
        "status": run.status.value,
        "findings_count": run.findings_count,
        "uncertainty_score": run.uncertainty_score,
        "created_at": run.created_at.isoformat(),
    }


@router.get("/companies/{company_id}/health")
async def get_company_health(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    service = CompanyIntelligenceService(repo)
    health = await service.assess_company_health(company_id)
    return {
        "id": health.id,
        "company_id": health.company_id,
        "overall_health_status": health.overall_health_status,
        "dimension_scores": health.dimension_scores,
        "key_findings": health.key_findings,
        "top_risks": health.top_risks,
        "top_opportunities": health.top_opportunities,
    }


@router.get("/companies/{company_id}/bottlenecks")
async def get_company_bottlenecks(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    service = CompanyIntelligenceService(repo)
    bottlenecks = await service.detect_bottlenecks(company_id)
    return [
        {
            "id": b.id,
            "bottleneck_name": b.bottleneck_name,
            "affected_scope": b.affected_scope,
            "severity": b.severity,
            "evidence_summary": b.evidence_summary,
            "suspected_causes": b.suspected_causes,
        }
        for b in bottlenecks
    ]


@router.get("/companies/{company_id}/risks")
async def get_company_risks(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    service = CompanyIntelligenceService(repo)
    risks = await service.assess_risks(company_id)
    return [
        {
            "id": r.id,
            "title": r.title,
            "category": r.category.value,
            "severity": r.severity,
            "probability_score": r.probability_score,
            "impact_score": r.impact_score,
            "mitigation_options": r.mitigation_options,
        }
        for r in risks
    ]


@router.post("/companies/{company_id}/decision-questions", status_code=status.HTTP_201_CREATED)
async def create_decision_question(
    company_id: str,
    payload: DecisionQuestionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    service = DecisionSupportService(repo)
    question = await service.create_decision_question(
        company_id=company_id,
        question=payload.question,
        purpose=payload.purpose,
        scope=payload.scope,
        urgency=payload.urgency,
        constraints=payload.constraints,
    )
    return {
        "id": question.id,
        "company_id": question.company_id,
        "question": question.question,
        "urgency": question.urgency.value,
    }


@router.post("/companies/{company_id}/decision-questions/{question_id}/evaluate")
async def evaluate_decision_question(
    company_id: str,
    question_id: str,
    payload: EvaluateOptionsRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    service = DecisionSupportService(repo)
    options = await service.generate_decision_options(question_id, payload.options_data)
    evaluations = await service.evaluate_decision_options(question_id)
    insight = await service.synthesize_decision_insight(question_id)
    return {
        "insight_id": insight.id,
        "question_id": insight.question_id,
        "version": insight.version,
        "options_count": len(options),
        "recommendation_summary": insight.recommendation_summary,
        "recommended_option_id": insight.recommended_option_id,
        "governance_required": insight.governance_required,
    }


@router.get("/companies/{company_id}/decision-insights/{insight_id}")
async def get_decision_insight(
    company_id: str,
    insight_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    insight = await repo.get_decision_insight_by_id(insight_id)
    if not insight or insight.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision insight not found.")
    return {
        "id": insight.id,
        "question_id": insight.question_id,
        "company_id": insight.company_id,
        "version": insight.version,
        "evidence_graph": insight.evidence_graph,
        "options": insight.options,
        "tradeoffs": insight.tradeoffs,
        "recommendation_summary": insight.recommendation_summary,
        "recommended_option_id": insight.recommended_option_id,
        "governance_required": insight.governance_required,
        "governance_approval_id": insight.governance_approval_id,
        "is_executed": insight.is_executed,
    }


@router.post("/companies/{company_id}/decision-insights/{insight_id}/execute")
async def execute_decision_insight(
    company_id: str,
    insight_id: str,
    payload: ExecuteInsightRequest,
    x_user_id: Optional[str] = Header("SYSTEM", alias="X-User-ID"),
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    insight = await repo.get_decision_insight_by_id(insight_id)
    if not insight or insight.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision insight not found.")
    bridge_svc = DecisionExecutionBridgeService(repo)
    try:
        exec_payload = await bridge_svc.execute_decision_insight(
            insight_id=insight_id,
            actor_id=x_user_id or "SYSTEM",
            governance_approval_id=payload.governance_approval_id,
        )
        return exec_payload
    except UnauthorizedDecisionExecutionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except DecisionInsightExpiredError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/companies/{company_id}/decision-outcomes/evaluate", status_code=status.HTTP_201_CREATED)
async def evaluate_decision_outcome(
    company_id: str,
    payload: EvaluateOutcomeRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyCompanyIntelligenceRepository(db)
    learning_svc = DecisionOutcomeLearningService(repo)
    outcome = await learning_svc.evaluate_decision_outcome(
        insight_id=payload.insight_id,
        company_id=company_id,
        executed_option_id=payload.executed_option_id,
        expected_outcomes=payload.expected_outcomes,
        actual_outcomes=payload.actual_outcomes,
    )
    return {
        "id": outcome.id,
        "insight_id": outcome.insight_id,
        "variance_analysis": outcome.variance_analysis,
        "learning_candidate": outcome.learning_candidate,
        "knowledge_item_id": outcome.knowledge_item_id,
    }
