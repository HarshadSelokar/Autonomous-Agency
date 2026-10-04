"""
FastAPI Routes for Phase 12 Model Routing.
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas.model_routing import (
    ModelProfileCreateSchema,
    ModelProviderHealthUpdateSchema,
    ModelRouteRequestSchema,
    ModelSelectionDecisionResponseSchema,
)
from src.application.model_router import ModelRouter
from src.domain.model_routing import (
    ModelCapability,
    ModelSelectionRequest,
    RoutingStrategy,
)
from src.infrastructure.database import get_db, run_with_sync_session
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository

router = APIRouter(prefix="/models", tags=["Model Routing"])


def _router(session: Session) -> ModelRouter:
    return ModelRouter(repository=ModelRoutingRepository(session))


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_model_profile(
    payload: ModelProfileCreateSchema,
    db: Any = Depends(get_db),
) -> dict[str, str]:
    caps = [ModelCapability(c) for c in payload.capabilities]
    profile = await run_with_sync_session(db, lambda session: _router(session).register_model_profile(
        model_id=payload.model_id,
        provider_name=payload.provider_name,
        model_name=payload.model_name,
        capabilities=caps,
        context_window_tokens=payload.context_window_tokens,
        cost_per_1k_input_tokens=payload.cost_per_1k_input_tokens,
        cost_per_1k_output_tokens=payload.cost_per_1k_output_tokens,
        latency_ms=payload.latency_ms,
        quality_score=payload.quality_score,
        is_active=payload.is_active,
        is_approved_for_production=payload.is_approved_for_production,
    ))
    return {"model_id": profile.model_id, "status": "REGISTERED"}


@router.post("/route", response_model=ModelSelectionDecisionResponseSchema)
async def route_model(
    payload: ModelRouteRequestSchema,
    db: Any = Depends(get_db),
) -> ModelSelectionDecisionResponseSchema:
    caps = [ModelCapability(c) for c in payload.required_capabilities]
    request = ModelSelectionRequest(
        request_id=f"req-api",
        task_id=payload.task_id,
        agent_id=payload.agent_id,
        required_capabilities=caps,
        strategy=RoutingStrategy(payload.strategy),
        max_budget_per_run=payload.max_budget_per_run,
        max_latency_ms=payload.max_latency_ms,
        min_quality_score=payload.min_quality_score,
        governance_risk_level=payload.governance_risk_level,
        allowlist_models=payload.allowlist_models,
        blocklist_models=payload.blocklist_models,
    )

    try:
        decision = await run_with_sync_session(
            db, lambda session: _router(session).route_model(request)
        )
        return ModelSelectionDecisionResponseSchema(
            decision_id=decision.decision_id,
            request_id=decision.request_id,
            task_id=decision.task_id,
            selected_model_id=decision.selected_model_id,
            selected_provider_name=decision.selected_provider_name,
            strategy_used=decision.strategy_used.value if hasattr(decision.strategy_used, "value") else str(decision.strategy_used),
            candidate_model_ids=decision.candidate_model_ids,
            rejected_candidates=decision.rejected_candidates,
            score_breakdown=decision.score_breakdown,
            is_fallback=decision.is_fallback,
            rationale=decision.rationale,
            created_at=str(decision.created_at),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/health", status_code=status.HTTP_200_OK)
async def update_health(
    payload: ModelProviderHealthUpdateSchema,
    db: Any = Depends(get_db),
) -> dict[str, str]:
    health = await run_with_sync_session(db, lambda session: _router(session).update_provider_health(
        provider_name=payload.provider_name,
        model_id=payload.model_id,
        is_healthy=payload.is_healthy,
        error_rate=payload.error_rate,
        latency_p95_ms=payload.latency_p95_ms,
        last_failure_reason=payload.last_failure_reason,
    ))
    return {"model_id": health.model_id, "status": "UPDATED", "is_healthy": str(health.is_healthy)}
