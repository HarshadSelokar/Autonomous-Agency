"""FastAPI Routes for Phase 19 Research, Discovery & Autonomous Research Services."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.research import (
    AddEvidenceRequest,
    CreateResearchPlanRequest,
    CreateResearchRequest,
    DecomposeRequestSchema,
    EvaluateHypothesisRequest,
    FormulateHypothesisRequest,
    RegisterSourceRequest,
    ResearchRequestResponse,
    SynthesizeFindingRequest,
)
from src.application.research_services import (
    ResearchEvidenceService,
    ResearchHypothesisService,
    ResearchPlanningService,
    ResearchSourceService,
)
from src.domain.research import (
    ResearchRequest,
    ResearchScope,
    SourceType,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository
from src.infrastructure.repositories.research_repository import SQLAlchemyResearchRepository

router = APIRouter(prefix="/research", tags=["Autonomous Research"])


def _to_request_response(req: ResearchRequest) -> ResearchRequestResponse:
    return ResearchRequestResponse(
        id=req.id,
        question=req.question,
        purpose=req.purpose,
        scope=req.scope.value if hasattr(req.scope, "value") else str(req.scope),
        urgency=req.urgency,
        requester_id=req.requester_id,
        source_origin=req.source_origin,
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        governance_required=req.governance_required,
        created_at=req.created_at,
    )


@router.post("/requests", response_model=ResearchRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_research_request(
    payload: CreateResearchRequest,
    db: AsyncSession = Depends(get_db),
) -> ResearchRequestResponse:
    repo = SQLAlchemyResearchRepository(db)
    svc = ResearchPlanningService(repo)
    try:
        scope_enum = ResearchScope(payload.scope.upper())
    except ValueError:
        scope_enum = ResearchScope.COMPANY

    req = await svc.create_request(
        question=payload.question,
        purpose=payload.purpose,
        scope=scope_enum,
        urgency=payload.urgency,
        requester_id=payload.requester_id,
        source_origin=payload.source_origin,
        governance_required=payload.governance_required,
    )
    await db.commit()
    return _to_request_response(req)


@router.get("/requests", response_model=list[ResearchRequestResponse])
async def list_research_requests(
    db: AsyncSession = Depends(get_db),
) -> list[ResearchRequestResponse]:
    repo = SQLAlchemyResearchRepository(db)
    requests = await repo.list_requests()
    return [_to_request_response(r) for r in requests]


@router.post("/requests/{request_id}/decompose", status_code=status.HTTP_200_OK)
async def decompose_research_request(
    request_id: str,
    payload: DecomposeRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    svc = ResearchPlanningService(repo)
    try:
        questions = await svc.decompose_request_into_questions(
            request_id=request_id,
            sub_questions=payload.sub_questions,
        )
        await db.commit()
        return {
            "request_id": request_id,
            "question_count": len(questions),
            "questions": [{"id": q.id, "question": q.question} for q in questions],
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_research_plan(
    payload: CreateResearchPlanRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    svc = ResearchPlanningService(repo)
    try:
        plan = await svc.create_research_plan(
            question_id=payload.question_id,
            title=payload.title,
            objective=payload.objective,
            required_capabilities=payload.required_capabilities,
        )
        await db.commit()
        return {
            "id": plan.id,
            "question_id": plan.question_id,
            "title": plan.title,
            "status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def register_research_source(
    payload: RegisterSourceRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    svc = ResearchSourceService(repo)
    try:
        stype = SourceType(payload.source_type.upper())
    except ValueError:
        stype = SourceType.TECHNICAL_DOCUMENTATION

    source = await svc.register_source(
        location=payload.location,
        source_type=stype,
        provenance=payload.provenance,
        raw_content=payload.raw_content,
        is_external=payload.is_external,
    )
    await db.commit()
    return {
        "id": source.id,
        "location": source.location,
        "is_untrusted": source.is_untrusted,
        "prompt_injection_checked": source.prompt_injection_checked,
        "reliability_score": source.reliability_score,
    }


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
async def add_research_evidence(
    payload: AddEvidenceRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    svc = ResearchEvidenceService(repo)
    try:
        evidence = await svc.add_evidence(
            source_id=payload.source_id,
            content_snippet=payload.content_snippet,
            data_points=payload.data_points,
        )
        await db.commit()
        return {
            "id": evidence.id,
            "source_id": evidence.source_id,
            "integrity_hash": evidence.integrity_hash,
            "is_independent": evidence.is_independent,
            "corroboration_count": evidence.corroboration_count,
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/findings", status_code=status.HTTP_201_CREATED)
async def synthesize_research_finding(
    payload: SynthesizeFindingRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    svc = ResearchEvidenceService(repo)
    try:
        finding = await svc.synthesize_finding(
            question_id=payload.question_id,
            finding_statement=payload.finding_statement,
            evidence_ids=payload.evidence_ids,
            confidence=payload.confidence,
            researcher_id=payload.researcher_id,
        )
        await db.commit()
        return {
            "id": finding.id,
            "question_id": finding.question_id,
            "finding_statement": finding.finding_statement,
            "evidence_count": len(finding.evidence_ids),
            "confidence": finding.confidence,
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/hypotheses", status_code=status.HTTP_201_CREATED)
async def formulate_hypothesis(
    payload: FormulateHypothesisRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    svc = ResearchHypothesisService(repo)
    hyp = await svc.formulate_hypothesis(
        question_id=payload.question_id,
        observation=payload.observation,
        statement=payload.statement,
        prediction=payload.prediction,
    )
    await db.commit()
    return {
        "id": hyp.id,
        "question_id": hyp.question_id,
        "statement": hyp.statement,
        "status": hyp.status.value if hasattr(hyp.status, "value") else str(hyp.status),
    }


@router.post("/hypotheses/{hypothesis_id}/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_hypothesis(
    hypothesis_id: str,
    payload: EvaluateHypothesisRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = SQLAlchemyResearchRepository(db)
    k_repo = SQLAlchemyKnowledgeRepository(db)
    svc = ResearchHypothesisService(repo, knowledge_repository=k_repo)
    try:
        hyp = await svc.evaluate_hypothesis_result(
            hypothesis_id=hypothesis_id,
            result_description=payload.result_description,
            conclusion=payload.conclusion,
            is_supported=payload.is_supported,
        )
        await db.commit()
        return {
            "id": hyp.id,
            "status": hyp.status.value if hasattr(hyp.status, "value") else str(hyp.status),
            "conclusion": hyp.conclusion,
            "promoted_to_knowledge": payload.is_supported,
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
