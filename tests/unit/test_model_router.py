"""
Unit tests for ModelRouter (Phase 12).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.infrastructure.models  # noqa: F401
from src.application.model_router import ModelRouter
from src.domain.model_routing import (
    ModelCapability,
    ModelSelectionRequest,
    RoutingStrategy,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository


@pytest.fixture
def model_router():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = ModelRoutingRepository(session)
    router = ModelRouter(repository=repo)

    # Register sample model profiles
    router.register_model_profile(
        model_id="groq-llama-70b",
        provider_name="groq",
        model_name="llama-3.3-70b-versatile",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
        quality_score=0.95,
        cost_per_1k_input_tokens=0.002,
        latency_ms=180,
    )
    router.register_model_profile(
        model_id="fake-fast-model",
        provider_name="fake",
        model_name="fake-fast",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.FAST_RESPONSE],
        quality_score=0.75,
        cost_per_1k_input_tokens=0.0001,
        latency_ms=50,
    )
    return router


def test_capability_based_routing(model_router):
    req = ModelSelectionRequest(
        request_id="req-code",
        task_id="task-code-1",
        required_capabilities=[ModelCapability.CODE_GENERATION],
        strategy=RoutingStrategy.CAPABILITY_BASED,
    )
    decision = model_router.route_model(req)
    assert decision.selected_model_id == "groq-llama-70b"
    assert "fake-fast-model" in decision.rejected_candidates


def test_cost_aware_routing(model_router):
    req = ModelSelectionRequest(
        request_id="req-cost",
        task_id="task-text-1",
        required_capabilities=[ModelCapability.TEXT_GENERATION],
        strategy=RoutingStrategy.COST_AWARE,
    )
    decision = model_router.route_model(req)
    assert decision.selected_model_id == "fake-fast-model"


def test_health_fallback_routing(model_router):
    # Mark primary model as unhealthy
    model_router.update_provider_health("groq", "groq-llama-70b", is_healthy=False, last_failure_reason="503 Service Unavailable")

    req = ModelSelectionRequest(
        request_id="req-fallback",
        task_id="task-text-2",
        required_capabilities=[ModelCapability.TEXT_GENERATION],
        strategy=RoutingStrategy.QUALITY_AWARE,
    )
    decision = model_router.route_model(req)
    assert decision.selected_model_id == "fake-fast-model"
    assert "groq-llama-70b" in decision.rejected_candidates
