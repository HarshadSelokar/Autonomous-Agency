"""Unit tests for CompanyOperatingCycleService, Observation, Intelligence, and Executive services."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.company_observation_service import CompanyObservationService
from src.application.company_operating_cycle_service import CompanyOperatingCycleService
from src.application.executive_orchestration_service import ExecutiveOrchestrationService
from src.application.strategic_intelligence_service import StrategicIntelligenceService
from src.domain.company import AutonomousCompany, CompanyHealthStatus, CompanyStatus, OperatingCycleState
from src.domain.strategy import StrategyProposalType
from src.infrastructure.database import Base
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def setup_company(db_session):
    repo = SQLAlchemyCompanyRepository(db_session)
    comp = AutonomousCompany(
        id="comp-test-1",
        name="Test Autonomous Company",
        code="TESTCO",
        mission="Build reliable enterprise software",
        status=CompanyStatus.ACTIVE,
    )
    await repo.save_company(comp)
    return repo, comp


@pytest.mark.asyncio
async def test_company_observation_service(setup_company):
    repo, comp = setup_company
    obs_svc = CompanyObservationService(repo)

    kpis = await obs_svc.generate_kpi_snapshots(comp.id)
    assert len(kpis) == 6

    health = await obs_svc.evaluate_company_health(comp.id, kpis)
    assert health.overall_status in [CompanyHealthStatus.HEALTHY, CompanyHealthStatus.BALANCED]

    risks, opps = await obs_svc.identify_risks_and_opportunities(comp.id, health)
    assert isinstance(risks, list)
    assert isinstance(opps, list)


@pytest.mark.asyncio
async def test_strategic_intelligence_service(setup_company):
    repo, comp = setup_company
    strat_svc = StrategicIntelligenceService(repo)

    analysis = await strat_svc.analyze_strategic_situation(comp.id)
    assert analysis.company_id == comp.id
    assert analysis.confidence > 0.5

    proposal = await strat_svc.create_strategy_proposal(
        company_id=comp.id,
        proposal_type=StrategyProposalType.ORGANIZATIONAL_EVOLUTION,
        title="Form Specialized AI Safety Guild",
        proposal_body="Establish safety sub-guild",
        reason="Heightened compliance requirements",
    )
    assert proposal.title == "Form Specialized AI Safety Guild"

    # Verify simulation invariant (is_authoritative = False)
    sim = await strat_svc.run_what_if_simulation(
        company_id=comp.id,
        title="Simulate 2x Workforce Increase",
        assumptions=["Double engineering capacity"],
        input_parameters={"headcount": 50},
    )
    assert sim.is_authoritative is False


@pytest.mark.asyncio
async def test_company_operating_cycle_full_flow(setup_company):
    repo, comp = setup_company
    obs_svc = CompanyObservationService(repo)
    strat_svc = StrategicIntelligenceService(repo)
    cycle_svc = CompanyOperatingCycleService(repo, obs_svc, strat_svc)

    completed_cycle = await cycle_svc.execute_full_cycle(
        company_id=comp.id,
        initiated_by_id="exec-1",
        metric_values={"task_success_rate": 97.0, "delivery_velocity": 92.0},
    )

    assert completed_cycle.state == OperatingCycleState.COMPLETED
    assert completed_cycle.cycle_number == 1
    assert completed_cycle.completed_at is not None


@pytest.mark.asyncio
async def test_company_operating_cycle_pause_resume(setup_company):
    repo, comp = setup_company
    obs_svc = CompanyObservationService(repo)
    strat_svc = StrategicIntelligenceService(repo)
    cycle_svc = CompanyOperatingCycleService(repo, obs_svc, strat_svc)

    cycle = await cycle_svc.start_new_cycle(comp.id)
    await cycle_svc.transition_phase(cycle.id, OperatingCycleState.OBSERVING)

    paused = await cycle_svc.pause_cycle(cycle.id, "Awaiting market feedback")
    assert paused.state == OperatingCycleState.PAUSED

    resumed = await cycle_svc.resume_cycle(cycle.id)
    assert resumed.state == OperatingCycleState.OBSERVING


@pytest.mark.asyncio
async def test_executive_orchestration_service(setup_company):
    repo, comp = setup_company
    exec_svc = ExecutiveOrchestrationService(repo)

    report = await exec_svc.generate_executive_report(comp.id)
    assert report["company_name"] == "Test Autonomous Company"

    item = await exec_svc.add_portfolio_item(comp.id, "Platform Migration", "proj-999")
    assert item.status == "ACTIVE"

    updated_item = await exec_svc.update_portfolio_progress(item.id, 100.0, 95.0)
    assert updated_item.status == "COMPLETED"

    plan = await exec_svc.create_resource_allocation_plan(
        comp.id, None, "Q3 Eng Allocation", {"eng": 100000}
    )
    approved_plan = await exec_svc.approve_resource_allocation_plan(plan.id, "exec-boss")
    assert approved_plan.is_approved is True
