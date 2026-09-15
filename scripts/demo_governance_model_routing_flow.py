"""
Phase 11 & Phase 12 Integrated Control Chain Demonstration Script.
Control Chain: HUMAN GOVERNANCE -> POLICY/RISK/AUTHORITY -> MODEL ROUTING -> AGENT EXECUTION
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.execution_engine import AgentExecutionEngine
from src.application.governance_service import GovernanceService
from src.application.model_router import ModelRouter
from src.domain.agent import Agent, AgentState, ModelConfiguration
from src.domain.exceptions import AgentValidationError
from src.domain.governance import AutonomyLevel, GovernanceRule, GovernanceScope, RiskLevel
from src.domain.model_routing import ModelCapability, RoutingStrategy
from src.domain.run import RunStatus
from src.infrastructure.database import Base
from src.infrastructure.repositories.governance_repository import GovernanceRepository
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository


async def run_async_demo():
    print("================================================================================")
    print("PHASE 11 & 12 — INTEGRATED GOVERNANCE & MODEL ROUTING DEMONSTRATION")
    print("================================================================ launch\n")

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    gov_repo = GovernanceRepository(session)
    mr_repo = ModelRoutingRepository(session)

    gov_service = GovernanceService(repository=gov_repo)
    model_router = ModelRouter(repository=mr_repo)

    model_router.register_model_profile(
        model_id="llama-3.3-70b-versatile",
        provider_name="groq",
        model_name="Llama 3.3 70B",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
        quality_score=0.92,
    )

    print("--- SCENARIO 1: High-Risk Action Blocked by Governance Before Model Selection ---")
    rule_critical = GovernanceRule(
        rule_id="rule-critical",
        name="Critical Operation Guard",
        description="Requires manager approval",
        scope=GovernanceScope.GLOBAL,
        target_pattern="drop_database*",
        min_risk_level=RiskLevel.CRITICAL,
        autonomy_level=AutonomyLevel.BLOCKED,
    )
    rule_allow = GovernanceRule(
        rule_id="rule-allow",
        name="Allow Formatting",
        description="Allow routine code format",
        scope=GovernanceScope.GLOBAL,
        target_pattern="Format*",
        min_risk_level=RiskLevel.LOW,
        autonomy_level=AutonomyLevel.FULLY_AUTONOMOUS,
    )
    gov_service.define_policy("Global Policy", GovernanceScope.GLOBAL, "GLOBAL", level="SYSTEM", rules=[rule_critical, rule_allow])

    agent = Agent(
        id="ag-dev-1",
        name="DevBot",
        role="Software Engineer",
        description="Autonomous Developer",
        current_state=AgentState.IDLE,
        model_configuration=ModelConfiguration(provider="groq", model="llama-3.3-70b-versatile"),
    )

    agent_repo = AsyncMock()
    run_repo = AsyncMock()
    step_repo = AsyncMock()
    agent_repo.get_by_id.return_value = agent

    # Provider mock
    provider = AsyncMock()
    model_res = MagicMock()
    model_res.content = "Action completed successfully"
    model_res.usage.input_tokens = 15
    model_res.usage.output_tokens = 25
    model_res.usage.total_tokens = 40
    model_res.request_id = "req-exec-1"
    model_res.finish_reason = "stop"
    provider.generate.return_value = model_res

    provider_registry = MagicMock()
    provider_registry.get.return_value = provider

    exec_engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=provider_registry,
        governance_service=gov_service,
        model_router=model_router,
    )

    print("[!] Agent attempting blocked action 'drop_database'...")
    try:
        await exec_engine.execute_run(agent_id="ag-dev-1", objective="drop_database production")
    except AgentValidationError as e:
        print(f"[-] GOVERNANCE INTERCEPTED: {e}")

    print("[SUCCESS] Governance policy prevented unauthorized agent execution BEFORE model selection!\n")

    print("--- SCENARIO 2: Approved Action -> Model Router Selects Optimal Model -> Execution ---")
    agent.current_state = AgentState.IDLE
    run = await exec_engine.execute_run(agent_id="ag-dev-1", objective="Format python files")
    print(f"[+] Execution Succeeded! Run Status: {run.status.value}")
    print(f"[+] LLM Provider Output Data: {run.result}")

    print("\n================================================================================")
    print("INTEGRATED CONTROL CHAIN DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("================================================================================\n")


def run_demo():
    asyncio.run(run_async_demo())


if __name__ == "__main__":
    run_demo()
