"""
Unit tests for Model Routing Domain Model (Phase 12).
"""

import pytest
from src.domain.model_routing import (
    ModelCapability,
    ModelProfile,
    ModelSelectionDecision,
    ModelSelectionRequest,
    RoutingStrategy,
)


def test_model_profile_capabilities():
    mp = ModelProfile(
        model_id="groq-llama-70b",
        provider_name="groq",
        model_name="llama-3.3-70b-versatile",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
    )

    assert mp.has_capability(ModelCapability.CODE_GENERATION)
    assert mp.has_capability(ModelCapability.REASONING)
    assert not mp.has_capability(ModelCapability.VISION)


def test_model_selection_decision_structure():
    decision = ModelSelectionDecision(
        decision_id="dec-1",
        request_id="req-1",
        task_id="t-100",
        selected_model_id="groq-llama-70b",
        selected_provider_name="groq",
        strategy_used=RoutingStrategy.QUALITY_AWARE,
        candidate_model_ids=["groq-llama-70b", "fake-model-1"],
        rationale="Selected highest quality coding model within budget",
    )

    assert decision.selected_model_id == "groq-llama-70b"
    assert not decision.is_fallback
    assert len(decision.candidate_model_ids) == 2
