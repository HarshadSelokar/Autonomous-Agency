"""
Unit tests for Agent Runtime integration with ToolContextProvider and ToolExecutionPipeline.
"""

from typing import Any
import pytest

from src.application.context import ContextBuilder, ToolContextProvider
from src.application.execution_engine import AgentExecutionEngine
from src.application.tool_execution_pipeline import ToolExecutionPipeline
from src.application.tool_registry import ToolRegistry
from src.domain.agent import Agent, AgentState, ModelConfiguration, PermissionProfile, VerificationPolicy
from src.domain.model_provider import ModelResponse, UsageInfo
from src.domain.tool import PermissionMode, ToolCapability, ToolCategory, ToolDefinition
from src.infrastructure.models.fake_provider import FakeModelProvider


class InMemoryAgentRepository:
    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}

    async def get_by_id(self, agent_id: str) -> Agent | None:
        return self.agents.get(agent_id)

    async def save(self, agent: Agent) -> Agent:
        self.agents[agent.id] = agent
        return agent


class InMemoryRunRepository:
    def __init__(self) -> None:
        self.runs: dict[str, Any] = {}

    async def save(self, run: Any) -> Any:
        self.runs[run.id] = run
        return run

    async def get_by_id(self, run_id: str) -> Any:
        return self.runs.get(run_id)


class InMemoryStepRepository:
    def __init__(self) -> None:
        self.steps: list[Any] = []

    async def save(self, step: Any) -> Any:
        self.steps.append(step)
        return step


@pytest.mark.asyncio
async def test_agent_runtime_tool_context_and_execution() -> None:
    # 1. Register Tool
    registry = ToolRegistry()
    tool_def = ToolDefinition(
        id="workspace_file_reader",
        name="Workspace File Reader",
        description="Reads workspace files safely",
        category=ToolCategory.FILESYSTEM,
        capabilities=[ToolCapability.READ_FILE],
        permission_mode=PermissionMode.AUTO,
    )
    registry.register(tool_def)

    pipeline = ToolExecutionPipeline(registry=registry)
    context_builder = ContextBuilder(providers=[ToolContextProvider(registry)])

    agent_repo = InMemoryAgentRepository()
    run_repo = InMemoryRunRepository()
    step_repo = InMemoryStepRepository()

    from pathlib import Path
    Path("scratch").mkdir(exist_ok=True)
    (Path("scratch") / "test.txt").write_text("Hello file content", encoding="utf-8")

    agent = Agent(
        id="agent-tool-dev",
        name="Tool Agent",
        role="Developer",
        description="Executes tools",
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
        permission_profile=PermissionProfile(permissions=["execute_tools"]),
        verification_policy=VerificationPolicy(required=False),
        current_state=AgentState.IDLE,
    )
    await agent_repo.save(agent)

    # Fake Provider returning a structured tool request
    fake_provider = FakeModelProvider(
        canned_content='{"tool_request": {"tool_id": "workspace_file_reader", "capability": "READ_FILE", "arguments": {"path": "test.txt"}}}',
        canned_structured_output={
            "tool_request": {
                "tool_id": "workspace_file_reader",
                "capability": "READ_FILE",
                "arguments": {"path": "test.txt"},
            }
        },
    )

    from src.application.provider_registry import ModelProviderRegistry
    registry_provider = ModelProviderRegistry()
    registry_provider.register(fake_provider)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry_provider,
        context_builder=context_builder,
        tool_pipeline=pipeline,
    )

    run = await engine.execute_run(
        agent_id="agent-tool-dev",
        objective="Read file test.txt",
    )

    assert run.status.value == "COMPLETED"
    assert "tool_result" in run.result
    tool_res = run.result["tool_result"]
    assert tool_res is not None
    assert tool_res["status"] == "SUCCEEDED"
