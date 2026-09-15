"""
Repository implementation for Phase 12 Model Routing entities.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.model_routing import (
    ModelCapability,
    ModelProfile,
    ModelProviderHealth,
    ModelSelectionDecision,
    RoutingStrategy,
)
from src.infrastructure.models.model_routing_model import (
    ModelProfileModel,
    ModelProviderHealthModel,
    ModelSelectionDecisionModel,
)


class ModelRoutingRepository:
    def __init__(self, session: Session):
        self._session = session

    def save_model_profile(self, profile: ModelProfile) -> ModelProfile:
        caps_list = [c.value if hasattr(c, "value") else str(c) for c in profile.capabilities]
        model = ModelProfileModel(
            id=profile.model_id,
            provider_name=profile.provider_name,
            model_name=profile.model_name,
            capabilities=caps_list,
            context_window_tokens=profile.context_window_tokens,
            cost_per_1k_input_tokens=profile.cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=profile.cost_per_1k_output_tokens,
            latency_ms=profile.latency_ms,
            quality_score=profile.quality_score,
            is_active=profile.is_active,
            is_approved_for_production=profile.is_approved_for_production,
            created_at=profile.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return profile

    def get_model_profile(self, model_id: str) -> Optional[ModelProfileModel]:
        stmt = select(ModelProfileModel).where(ModelProfileModel.id == model_id)
        return self._session.scalars(stmt).first()

    def get_active_model_profiles(self) -> List[ModelProfileModel]:
        stmt = select(ModelProfileModel).where(ModelProfileModel.is_active.is_(True))
        return list(self._session.scalars(stmt).all())

    def save_routing_decision(self, decision: ModelSelectionDecision) -> ModelSelectionDecision:
        model = ModelSelectionDecisionModel(
            id=decision.decision_id,
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
            created_at=decision.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return decision

    def get_routing_decision(self, decision_id: str) -> Optional[ModelSelectionDecisionModel]:
        stmt = select(ModelSelectionDecisionModel).where(ModelSelectionDecisionModel.id == decision_id)
        return self._session.scalars(stmt).first()

    def save_provider_health(self, health: ModelProviderHealth) -> ModelProviderHealth:
        health_id = f"health-{health.provider_name}-{health.model_id}"
        model = ModelProviderHealthModel(
            id=health_id,
            provider_name=health.provider_name,
            model_id=health.model_id,
            is_healthy=health.is_healthy,
            error_rate=health.error_rate,
            latency_p95_ms=health.latency_p95_ms,
            rate_limit_reset_at=health.rate_limit_reset_at,
            last_failure_reason=health.last_failure_reason,
            updated_at=health.updated_at,
        )
        self._session.merge(model)
        self._session.commit()
        return health

    def get_provider_health(self, model_id: str) -> Optional[ModelProviderHealthModel]:
        stmt = select(ModelProviderHealthModel).where(ModelProviderHealthModel.model_id == model_id)
        return self._session.scalars(stmt).first()
