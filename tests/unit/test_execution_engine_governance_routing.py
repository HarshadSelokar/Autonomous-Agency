"""
Unit tests for AgentExecutionEngine integration with GovernanceService and ModelRouter (Phases 11 & 12).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.application.execution_engine import AgentExecutionEngine
from src.domain.agent import Agent, AgentState, ModelConfiguration
from src.domain.exceptions import AgentValidationError
from src.domain.governance import AutonomyLevel, RiskLevel
from src.domain.model_routing import ModelSelectionDecision, RoutingStrategy
from src.domain.run import AgentRun, RunStatus


@pytest.mark.asyncio
async def test_execution_engine_blocked_by_governance():
    agent_repo = AsyncMock()
    run_repo = AsyncMock()
    step_repo = AsyncMock()

    agent = Agent(
        id="ag-1",
        name="Worker Agent",
        role="Worker",
        description="Desc",
        current_state=AgentState.IDLE,
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
    )
    agent_repo.get_by_id.return_value = agent

    gov_service = MagicMock()
    gov_service.evaluate_autonomy.return_value = (AutonomyLevel.BLOCKED, RiskLevel.CRITICAL, None)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        governance_service=gov_service,
    )

    with pytest.raises(AgentValidationError, match="Execution blocked by Governance Policy"):
        await engine.execute_run(agent_id="ag-1", objective="Forbidden Objective")


@pytest.mark.asyncio
async def test_execution_engine_model_routing():
    agent_repo = AsyncMock()
    run_repo = AsyncMock()
    step_repo = AsyncMock()

    agent = Agent(
        id="ag-2",
        name="Router Worker Agent",
        role="Worker",
        description="Desc",
        current_state=AgentState.IDLE,
        model_configuration=ModelConfiguration(provider="fake", model="default-model"),
    )
    agent_repo.get_by_id.return_value = agent

    model_router = MagicMock()
    model_router.route_model.return_value = ModelSelectionDecision(
        decision_id="dec-99",
        request_id="req-99",
        task_id=None,
        selected_model_id="routed-super-model",
        selected_provider_name="fake",
        strategy_used=RoutingStrategy.QUALITY_AWARE,
    )

    provider = AsyncMock()
    model_res = MagicMock()
    model_res.content = "Routed response"
    model_res.usage.input_tokens = 10
    model_res.usage.output_tokens = 20
    model_res.usage.total_tokens = 30
    model_res.request_id = "req-1"
    model_res.finish_reason = "stop"
    provider.generate.return_value = model_res

    provider_registry = MagicMock()
    provider_registry.get.return_value = provider

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=provider_registry,
        model_router=model_router,
    )

    run = await engine.execute_run(agent_id="ag-2", objective="Test Model Router Selection")
    assert run.status == RunStatus.COMPLETED
    model_router.route_model.assert_called_once()
    provider_registry.get.assert_called_with("fake")
