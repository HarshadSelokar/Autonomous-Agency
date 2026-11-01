"""
Unit tests for Phase 36 Model Router V2 enhancements.
"""

import pytest
from unittest.mock import MagicMock
from src.application.model_router import ModelRouter
from src.domain.model_routing import (
    ModelCapability,
    ModelSelectionRequest,
    RoutingStrategy,
)


def test_select_model_v2_budget_and_complexity():
    repo_mock = MagicMock()

    m1 = MagicMock()
    m1.id = "groq-llama-70b"
    m1.provider_name = "groq"
    m1.model_name = "llama-3.3-70b-versatile"
    m1.capabilities = ["TEXT_GENERATION", "REASONING"]
    m1.context_window_tokens = 128000
    m1.cost_per_1k_input_tokens = 0.002
    m1.cost_per_1k_output_tokens = 0.004
    m1.latency_ms = 200
    m1.quality_score = 0.95
    m1.is_active = True
    m1.is_approved_for_production = True
    m1.created_at = None

    repo_mock.get_active_model_profiles.return_value = [m1]
    repo_mock.get_provider_health.return_value = MagicMock(is_healthy=True, error_rate=0.0)

    router = ModelRouter(repository=repo_mock)

    req = ModelSelectionRequest(
        request_id="req-1",
        required_capabilities=[ModelCapability.TEXT_GENERATION],
    )

    decision = router.select_model_v2(
        request=req,
        max_budget_cost=0.01,  # Tight budget triggers COST_AWARE
        task_complexity="HIGH",
        tenant_id="tenant-acme",
    )

    assert decision.selected_model_id == "groq-llama-70b"
    assert "tenant-acme" in decision.rationale
