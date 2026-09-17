"""
Integration Tests for Phase 25 Company Simulation Mode & Safety Isolation.

Verifies:
1. What-If Simulation scenario execution computes correct metric projections.
2. Simulation mode strictly blocks production mutation calls (SimulationProductionMutationError).
3. Production DB records remain unmutated by scenario engine runs.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.company import ExecutionEnvironment
from src.domain.simulation import CompanySimulation, SimulationStatus
from src.domain.exceptions import SimulationProductionMutationError
from src.infrastructure.database import Base
import src.infrastructure.models.company_model
from src.infrastructure.repositories.company_repository import SQLAlchemyMultiCompanyRepository
from src.application.company_service import CompanyService
from src.application.company_simulation_service import CompanySimulationService
from src.application.simulation_scenario_engine import SimulationScenarioEngine


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_simulation_safety_blocked_actions():
    sim = CompanySimulation(
        company_id="comp-prod-01",
        name="Test Simulation Sandbox",
        environment=ExecutionEnvironment.SIMULATION,
    )

    # Allowed non-mutation action
    sim.assert_simulation_safety("COMPUTE_SCENARIO_OUTCOMES")

    # Blocked production actions raise SimulationProductionMutationError
    blocked_actions = [
        "CHARGE_CREDIT_CARD",
        "SEND_EXTERNAL_EMAIL",
        "MUTATE_PRODUCTION_DATABASE",
        "EXECUTE_PRODUCTION_DEPLOYMENT",
    ]
    for action in blocked_actions:
        with pytest.raises(SimulationProductionMutationError):
            sim.assert_simulation_safety(action)


@pytest.mark.asyncio
async def test_simulation_scenario_execution_and_production_isolation(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)
    company_svc = CompanyService(repo)
    sim_svc = CompanySimulationService(repo)
    engine = SimulationScenarioEngine(repo)

    # 1. Create Production Company
    company = await company_svc.create_company("Starlight Solar", "starlight-solar")

    # 2. Create Snapshot & Scenario
    snapshot = await sim_svc.create_snapshot(
        company_id=company.id,
        snapshot_name="Q3 Baseline",
        baseline_metrics={"revenue_cents": 10000000, "expenses_cents": 4000000, "headcount": 8, "customers": 20},
    )

    scenario = await sim_svc.create_scenario(
        company_id=company.id,
        name="2x Staffing Scenario",
        description="Doubling engineering team",
        variables={"headcount_multiplier": 2.0, "marketing_boost_pct": 25.0, "price_multiplier": 1.1},
    )

    simulation = await sim_svc.create_simulation(
        company_id=company.id,
        name="Staffing Expansion Run",
        scenario_id=scenario.id,
        snapshot_id=snapshot.id,
    )

    # 3. Run Scenario Engine
    result = await engine.run_simulation(simulation.id)

    # 4. Verify Engine Output
    assert result.simulated_metrics["headcount"] == 16
    assert result.simulated_metrics["revenue_cents"] > result.baseline_metrics["revenue_cents"]
    assert result.variance_analysis["revenue_delta_pct"] > 0.0

    # 5. Verify Production Company state remains untouched
    db_company = await repo.get_company_by_id(company.id)
    assert db_company.id == company.id
    assert db_company.lifecycle == company.lifecycle
