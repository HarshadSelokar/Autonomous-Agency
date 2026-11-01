"""
ModelRouter Application Service for Phase 12 Model Routing & Intelligent Model Selection.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from src.domain.events import (
    DomainEvent,
    ModelFallbackUsedEvent,
    ModelHealthChangedEvent,
    ModelSelectedEvent,
    ModelSelectionRequestedEvent,
    ModelUnavailableEvent,
)
from src.domain.model_routing import (
    ModelCapability,
    ModelProfile,
    ModelProviderHealth,
    ModelSelectionDecision,
    ModelSelectionRequest,
    RoutingStrategy,
)
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository


class ModelRouter:
    """Provider-neutral Model Router responsible for intelligent model selection, strategy-based scoring, governance allowlist validation, and controlled fallback."""

    def __init__(self, repository: Optional[ModelRoutingRepository] = None, outbox_publisher: Optional[Any] = None):
        self._repository = repository
        self._outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self._outbox_publisher and hasattr(self._outbox_publisher, "publish"):
            self._outbox_publisher.publish(event)

    def register_model_profile(
        self,
        model_id: str,
        provider_name: str,
        model_name: str,
        capabilities: List[ModelCapability],
        context_window_tokens: int = 128000,
        cost_per_1k_input_tokens: float = 0.001,
        cost_per_1k_output_tokens: float = 0.002,
        latency_ms: int = 200,
        quality_score: float = 0.90,
        is_active: bool = True,
        is_approved_for_production: bool = True,
    ) -> ModelProfile:
        profile = ModelProfile(
            model_id=model_id,
            provider_name=provider_name,
            model_name=model_name,
            capabilities=capabilities,
            context_window_tokens=context_window_tokens,
            cost_per_1k_input_tokens=cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=cost_per_1k_output_tokens,
            latency_ms=latency_ms,
            quality_score=quality_score,
            is_active=is_active,
            is_approved_for_production=is_approved_for_production,
        )
        self._repository.save_model_profile(profile)
        # Register default health record
        self.update_provider_health(provider_name, model_id, is_healthy=True)
        return profile

    def update_provider_health(
        self,
        provider_name: str,
        model_id: str,
        is_healthy: bool = True,
        error_rate: float = 0.0,
        latency_p95_ms: int = 250,
        last_failure_reason: Optional[str] = None,
    ) -> ModelProviderHealth:
        health = ModelProviderHealth(
            provider_name=provider_name,
            model_id=model_id,
            is_healthy=is_healthy,
            error_rate=error_rate,
            latency_p95_ms=latency_p95_ms,
            last_failure_reason=last_failure_reason,
            updated_at=datetime.now(timezone.utc),
        )
        self._repository.save_provider_health(health)
        self._publish_event(ModelHealthChangedEvent(model_id=model_id, provider_name=provider_name, is_healthy=is_healthy))
        return health

    def route_model(self, request: ModelSelectionRequest) -> ModelSelectionDecision:
        decision_id = f"dec-{uuid.uuid4().hex[:8]}"
        self._publish_event(ModelSelectionRequestedEvent(request_id=request.request_id, task_id=request.task_id, strategy=request.strategy.value))

        # 1. Fetch active model profiles
        models_data = self._repository.get_active_model_profiles()
        profiles: List[ModelProfile] = []
        for m in models_data:
            caps = [ModelCapability(c) for c in (m.capabilities if isinstance(m.capabilities, list) else [])]
            profiles.append(
                ModelProfile(
                    model_id=m.id,
                    provider_name=m.provider_name,
                    model_name=m.model_name,
                    capabilities=caps,
                    context_window_tokens=m.context_window_tokens,
                    cost_per_1k_input_tokens=m.cost_per_1k_input_tokens,
                    cost_per_1k_output_tokens=m.cost_per_1k_output_tokens,
                    latency_ms=m.latency_ms,
                    quality_score=m.quality_score,
                    is_active=m.is_active,
                    is_approved_for_production=m.is_approved_for_production,
                    created_at=m.created_at,
                )
            )

        if not profiles:
            raise ValueError("No active model profiles registered in system")

        rejected_candidates: Dict[str, str] = {}
        candidate_profiles: List[ModelProfile] = []

        # 2. Filter by governance allowlist / blocklist
        for p in profiles:
            if request.allowlist_models and p.model_id not in request.allowlist_models:
                rejected_candidates[p.model_id] = "Not in governance model allowlist"
                continue
            if request.blocklist_models and p.model_id in request.blocklist_models:
                rejected_candidates[p.model_id] = "Blocked by governance policy"
                continue
            if not p.is_approved_for_production and request.governance_risk_level in ("HIGH", "CRITICAL"):
                rejected_candidates[p.model_id] = "Not approved for production governance risk level"
                continue

            # Check required capabilities
            missing_caps = [c for c in request.required_capabilities if not p.has_capability(c)]
            if missing_caps:
                rejected_candidates[p.model_id] = f"Missing required capabilities: {[c.value for c in missing_caps]}"
                continue

            # Check provider health
            health_model = self._repository.get_provider_health(p.model_id)
            if health_model and not health_model.is_healthy:
                rejected_candidates[p.model_id] = f"Provider model unhealthy ({health_model.last_failure_reason or 'unresponsive'})"
                self._publish_event(ModelUnavailableEvent(model_id=p.model_id, provider_name=p.provider_name, reason="Unhealthy status"))
                continue

            candidate_profiles.append(p)

        if not candidate_profiles:
            # Fallback: relax health check if all models were filtered due to health
            fallback_candidates = [p for p in profiles if (not request.allowlist_models or p.model_id in request.allowlist_models) and all(p.has_capability(c) for c in request.required_capabilities)]
            if fallback_candidates:
                candidate_profiles = fallback_candidates
                is_fallback = True
            else:
                raise ValueError(f"No suitable model candidate found matching requirements: {request.required_capabilities}")
        else:
            is_fallback = False

        # 3. Score candidate profiles based on strategy
        scores: Dict[str, float] = {}
        for p in candidate_profiles:
            score = self._compute_score(p, request)
            scores[p.model_id] = score

        # Sort by score descending
        sorted_candidates = sorted(candidate_profiles, key=lambda p: scores[p.model_id], reverse=True)
        selected_model = sorted_candidates[0]

        decision = ModelSelectionDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            task_id=request.task_id,
            selected_model_id=selected_model.model_id,
            selected_provider_name=selected_model.provider_name,
            strategy_used=request.strategy,
            candidate_model_ids=[p.model_id for p in candidate_profiles],
            rejected_candidates=rejected_candidates,
            score_breakdown=scores,
            is_fallback=is_fallback,
            rationale=f"Selected model '{selected_model.model_id}' via {request.strategy.value} strategy with score {scores[selected_model.model_id]:.2f}",
        )

        self._repository.save_routing_decision(decision)
        self._publish_event(ModelSelectedEvent(decision_id=decision_id, selected_model_id=selected_model.model_id, provider_name=selected_model.provider_name, is_fallback=is_fallback))

        if is_fallback:
            self._publish_event(ModelFallbackUsedEvent(decision_id=decision_id, primary_model_id="", fallback_model_id=selected_model.model_id, reason="Primary models filtered by health/governance"))

        return decision

    def _compute_score(self, profile: ModelProfile, request: ModelSelectionRequest) -> float:
        base_quality = profile.quality_score * 100.0
        total_cost = profile.cost_per_1k_input_tokens + profile.cost_per_1k_output_tokens

        if request.strategy == RoutingStrategy.QUALITY_AWARE:
            return base_quality * 2.0
        elif request.strategy == RoutingStrategy.COST_AWARE:
            # High penalty for higher cost so cheaper models win
            cost_penalty = total_cost * 10000.0
            return 100.0 - cost_penalty + (profile.quality_score * 10.0)
        elif request.strategy == RoutingStrategy.LATENCY_AWARE:
            latency_penalty = (profile.latency_ms / 5.0)
            return 100.0 - latency_penalty + (profile.quality_score * 10.0)
        elif request.strategy == RoutingStrategy.HEALTH_AWARE:
            health = self._repository.get_provider_health(profile.model_id)
            error_penalty = (health.error_rate * 100.0) if health else 0.0
            return base_quality - error_penalty

        return base_quality

    def select_model_v2(
        self,
        request: Optional[ModelSelectionRequest] = None,
        max_budget_cost: Optional[float] = None,
        task_complexity: str = "MEDIUM",
        tenant_id: Optional[str] = None,
        task_type: str = "general",
        preferred_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Phase 36 Enhanced Model Routing: Supports budget ceilings, task complexity scaling,
        and tenant isolation constraints.
        """
        if request is not None and self._repository is not None:
            if max_budget_cost is not None and max_budget_cost < 0.05:
                request.strategy = RoutingStrategy.COST_AWARE
            elif task_complexity in ("HIGH", "CRITICAL"):
                request.strategy = RoutingStrategy.QUALITY_AWARE

            decision = self.route_model(request)
            if tenant_id:
                decision.rationale += f" [Tenant: {tenant_id}]"
            return decision

        # No routing table available: fall back to the configured default of a real provider
        from src.infrastructure.config import settings

        provider = preferred_provider or "groq"
        # An env file can set GROQ_MODEL to an empty string
        selected = settings.OPENAI_MODEL if provider == "openai" else (settings.GROQ_MODEL or "openai/gpt-oss-120b")
        return {
            "primary_model": selected,
            "provider": provider,
            "tenant_id": tenant_id,
            "complexity": task_complexity,
        }
