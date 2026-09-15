"""
Integration tests for ModelRoutingRepository (Phase 12).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.infrastructure.models  # noqa: F401
from src.domain.model_routing import (
    ModelCapability,
    ModelProfile,
    ModelProviderHealth,
    ModelSelectionDecision,
    RoutingStrategy,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_model_routing_repository(db_session):
    repo = ModelRoutingRepository(db_session)

    # 1. Model Profile
    profile = ModelProfile(
        model_id="groq-llama-70b",
        provider_name="groq",
        model_name="llama-3.3-70b-versatile",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
    )
    repo.save_model_profile(profile)
    p_fetched = repo.get_model_profile("groq-llama-70b")
    assert p_fetched is not None
    assert p_fetched.provider_name == "groq"

    # 2. Decision
    decision = ModelSelectionDecision(
        decision_id="dec-100",
        request_id="req-100",
        task_id="task-1",
        selected_model_id="groq-llama-70b",
        selected_provider_name="groq",
        strategy_used=RoutingStrategy.QUALITY_AWARE,
        candidate_model_ids=["groq-llama-70b"],
        rationale="Top score candidate",
    )
    repo.save_routing_decision(decision)
    d_fetched = repo.get_routing_decision("dec-100")
    assert d_fetched is not None
    assert d_fetched.selected_model_id == "groq-llama-70b"

    # 3. Provider Health
    health = ModelProviderHealth(
        provider_name="groq",
        model_id="groq-llama-70b",
        is_healthy=True,
        latency_p95_ms=180,
    )
    repo.save_provider_health(health)
    h_fetched = repo.get_provider_health("groq-llama-70b")
    assert h_fetched is not None
    assert h_fetched.is_healthy
