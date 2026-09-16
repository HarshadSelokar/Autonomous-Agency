"""FastAPI Routes for Phase 18 Organizational Experiments."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.knowledge import (
    CompleteExperimentRequest,
    ExperimentResponse,
    KnowledgeItemResponse,
    ProposeExperimentRequest,
    StartExperimentRequest,
)
from src.application.knowledge_validation_service import KnowledgeValidationService
from src.application.organizational_experiment_service import OrganizationalExperimentService
from src.domain.experiment import OrganizationalExperiment
from src.infrastructure.database import get_db
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository

router = APIRouter(prefix="/experiments", tags=["Organizational Experiments"])


def _to_exp_response(exp: OrganizationalExperiment) -> ExperimentResponse:
    return ExperimentResponse(
        id=exp.id,
        title=exp.title,
        hypothesis=exp.hypothesis,
        status=exp.status.value if hasattr(exp.status, "value") else str(exp.status),
        risk_level=exp.risk_level,
        is_isolated=exp.is_isolated,
        governance_approval_id=exp.governance_approval_id,
        treatment_params=exp.treatment_params,
        results=exp.results,
        conclusion=exp.conclusion,
        created_at=exp.created_at,
    )


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def propose_experiment(
    payload: ProposeExperimentRequest,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    val_svc = KnowledgeValidationService(repo)
    exp_svc = OrganizationalExperimentService(repo, val_svc)

    exp = await exp_svc.propose_experiment(
        title=payload.title,
        hypothesis=payload.hypothesis,
        scope=payload.scope,
        risk_level=payload.risk_level,
        baseline_metrics=payload.baseline_metrics,
        treatment_params=payload.treatment_params,
        success_criteria=payload.success_criteria,
    )
    await db.commit()
    return _to_exp_response(exp)


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentResponse]:
    repo = SQLAlchemyKnowledgeRepository(db)
    exps = await repo.list_experiments()
    return [_to_exp_response(e) for e in exps]


@router.get("/{exp_id}", response_model=ExperimentResponse)
async def get_experiment(
    exp_id: str,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    exp = await repo.get_experiment_by_id(exp_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{exp_id}' not found.")
    return _to_exp_response(exp)


@router.post("/{exp_id}/start", response_model=ExperimentResponse)
async def start_experiment(
    exp_id: str,
    payload: StartExperimentRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    val_svc = KnowledgeValidationService(repo)
    exp_svc = OrganizationalExperimentService(repo, val_svc)

    gov_id = payload.governance_approval_id if payload else None
    try:
        exp = await exp_svc.start_experiment(exp_id, governance_approval_id=gov_id)
        await db.commit()
        return _to_exp_response(exp)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{exp_id}/complete", response_model=ExperimentResponse)
async def complete_experiment(
    exp_id: str,
    payload: CompleteExperimentRequest,
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    val_svc = KnowledgeValidationService(repo)
    exp_svc = OrganizationalExperimentService(repo, val_svc)

    try:
        exp = await exp_svc.complete_experiment(
            exp_id,
            results=payload.results,
            conclusion=payload.conclusion,
        )
        await db.commit()
        return _to_exp_response(exp)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{exp_id}/promote", response_model=KnowledgeItemResponse)
async def promote_experiment_to_knowledge(
    exp_id: str,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeItemResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    val_svc = KnowledgeValidationService(repo)
    exp_svc = OrganizationalExperimentService(repo, val_svc)

    try:
        candidate = await exp_svc.convert_experiment_to_knowledge_candidate(exp_id)
        await db.commit()
        return KnowledgeItemResponse(
            id=candidate.id,
            statement=candidate.statement,
            knowledge_type=candidate.knowledge_type.value if hasattr(candidate.knowledge_type, "value") else str(candidate.knowledge_type),
            scope=candidate.scope.value if hasattr(candidate.scope, "value") else str(candidate.scope),
            authority=candidate.authority.value if hasattr(candidate.authority, "value") else str(candidate.authority),
            status=candidate.status.value if hasattr(candidate.status, "value") else str(candidate.status),
            confidence=candidate.confidence,
            created_at=candidate.created_at,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
