"""
Unit tests for Phase 25 Company Simulation Service & Scenario Engine.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.simulation import SimulationStatus
from src.domain.company import ExecutionEnvironment
from src.infrastructure.database import Base
import src.infrastructure.models.company_model
from src.infrastructure.repositories.company_repository import SQLAlchemyMultiCompanyRepository
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
async def test_company_simulation_and_scenario_engine(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)
    sim_svc = CompanySimulationService(repo)
    engine_svc = SimulationScenarioEngine(repo)

    company_id = "comp-sim-test-01"

    # 1. Create Baseline Snapshot
    snapshot = await sim_svc.create_snapshot(
        company_id=company_id,
        snapshot_name="2026 Q3 Baseline",
        baseline_metrics={
            "revenue_cents": 10000000,
            "expenses_cents": 5000000,
            "headcount": 10,
            "customers": 20,
        }
    )

    # 2. Create Scenario (50% headcount increase, 25% marketing boost)
    scenario = await sim_svc.create_scenario(
        company_id=company_id,
        name="Scaling Scenario",
        description="Simulate hiring 5 additional engineers and scaling marketing",
        variables={
            "headcount_multiplier": 1.5,
            "marketing_boost_pct": 25.0,
            "price_multiplier": 1.1,
        }
    )

    # 3. Create & Start Simulation
    simulation = await sim_svc.create_simulation(
        company_id=company_id,
        name="Q4 Growth Simulation Run",
        scenario_id=scenario.id,
        snapshot_id=snapshot.id,
    )
    assert simulation.status == SimulationStatus.READY
    assert simulation.environment == ExecutionEnvironment.SIMULATION

    started_sim = await sim_svc.start_simulation(simulation.id)
    assert started_sim.status == SimulationStatus.RUNNING

    # 4. Run Scenario Engine
    result = await engine_svc.run_simulation(simulation.id)
    assert result.scenario_name == "Scaling Scenario"
    assert result.simulated_metrics["headcount"] == 15
    assert result.simulated_metrics["customers"] == 25
    assert result.variance_analysis["revenue_delta_pct"] > 0

    # 5. Verify isolated simulation financial record
    fin_records = await repo.list_simulation_financial_records(simulation.id)
    assert len(fin_records) == 1
    assert fin_records[0].record_type == "SIMULATED_PROJECTED_REVENUE"
