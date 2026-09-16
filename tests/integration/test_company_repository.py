"""Integration tests for Phase 16 Autonomous Company Repository."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.company import (
    AutonomousCompany,
    CompanyHealthSnapshot,
    CompanyHealthStatus,
    CompanyKPISnapshot,
    CompanyOperatingCycle,
    CompanyOpportunity,
    CompanyRisk,
    CompanyStatus,
    ContinuousImprovementProposal,
    MetricTrend,
    OperatingCycleState,
    PortfolioItem,
    ResourceAllocationPlan,
    RiskSeverity,
)
from src.domain.strategy import (
    CompanyStrategy,
    StrategicAnalysis,
    StrategicInitiative,
    StrategicObjective,
    StrategyProposal,
    StrategyProposalStatus,
    StrategyProposalType,
    StrategySimulation,
    StrategyStatus,
)
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


@pytest.mark.asyncio
async def test_company_repository_crud(db_session):
    repo = SQLAlchemyCompanyRepository(db_session)

    # 1. Company
    company = AutonomousCompany(
        id="comp-1",
        name="AutoCorp AI",
        code="AUTOCORP",
        mission="Autonomous enterprise orchestration",
        status=CompanyStatus.ACTIVE,
    )
    saved_company = await repo.save_company(company)
    assert saved_company.id == "comp-1"
    fetched_company = await repo.get_company_by_id("comp-1")
    assert fetched_company is not None
    assert fetched_company.code == "AUTOCORP"

    fetched_by_code = await repo.get_company_by_code("AUTOCORP")
    assert fetched_by_code is not None
    assert fetched_by_code.id == "comp-1"

    # 2. Operating Cycle
    cycle = CompanyOperatingCycle(
        id="cycle-1",
        company_id="comp-1",
        cycle_number=1,
        state=OperatingCycleState.OBSERVING,
    )
    saved_cycle = await repo.save_cycle(cycle)
    assert saved_cycle.state == OperatingCycleState.OBSERVING

    active_cycle = await repo.get_active_cycle_for_company("comp-1")
    assert active_cycle is not None
    assert active_cycle.id == "cycle-1"

    # 3. Strategy
    strategy = CompanyStrategy(
        id="strat-1",
        company_id="comp-1",
        version=1,
        title="2026 Q3 Autonomous Growth",
        themes=["Market Expansion", "Operational Excellence"],
        status=StrategyStatus.ACTIVE,
    )
    saved_strategy = await repo.save_strategy(strategy)
    assert saved_strategy.version == 1

    active_strat = await repo.get_active_strategy_for_company("comp-1")
    assert active_strat is not None
    assert active_strat.title == "2026 Q3 Autonomous Growth"

    # 4. Objective & Initiative
    obj = StrategicObjective(
        id="obj-1",
        company_id="comp-1",
        title="Achieve 99% Delivery Accuracy",
        target_metric="delivery_accuracy",
        target_value=99.0,
    )
    await repo.save_objective(obj)
    objs = await repo.list_objectives_for_company("comp-1")
    assert len(objs) == 1

    init = StrategicInitiative(
        id="init-1",
        strategic_objective_id="obj-1",
        title="Autonomous QA Enforcement",
    )
    await repo.save_initiative(init)
    inits = await repo.list_initiatives_for_objective("obj-1")
    assert len(inits) == 1

    # 5. Metrics & Health
    metric = CompanyKPISnapshot(
        id="met-1",
        company_id="comp-1",
        metric_name="task_success_rate",
        value=98.5,
        target_value=99.0,
        trend=MetricTrend.UP,
    )
    await repo.save_metric_snapshot(metric)
    metrics = await repo.list_metric_snapshots_for_company("comp-1")
    assert len(metrics) == 1

    health = CompanyHealthSnapshot(
        id="health-1",
        company_id="comp-1",
        operational_health=0.95,
        overall_status=CompanyHealthStatus.HEALTHY,
        explanation="Systems operating cleanly",
    )
    await repo.save_health_snapshot(health)
    latest_health = await repo.get_latest_health_for_company("comp-1")
    assert latest_health is not None
    assert latest_health.overall_status == CompanyHealthStatus.HEALTHY

    # 6. Risk & Opportunity
    risk = CompanyRisk(
        id="risk-1",
        company_id="comp-1",
        title="Compute Cost Spike",
        severity=RiskSeverity.MEDIUM,
    )
    await repo.save_risk(risk)
    risks = await repo.list_risks_for_company("comp-1")
    assert len(risks) == 1

    opp = CompanyOpportunity(
        id="opp-1",
        company_id="comp-1",
        title="Cache Optimization",
        expected_value=15.0,
    )
    await repo.save_opportunity(opp)
    opps = await repo.list_opportunities_for_company("comp-1")
    assert len(opps) == 1

    # 7. Analysis & Proposal
    analysis = StrategicAnalysis(
        id="ana-1",
        company_id="comp-1",
        cycle_id="cycle-1",
        current_situation="Stable growth with minor latency",
    )
    await repo.save_analysis(analysis)
    analyses = await repo.list_analyses_for_company("comp-1")
    assert len(analyses) == 1

    prop = StrategyProposal(
        id="prop-1",
        company_id="comp-1",
        proposal_type=StrategyProposalType.ORGANIZATIONAL_EVOLUTION,
        title="Form Security Sub-department",
        proposal="Create dedicated security audit team",
        reason="Elevated risk profile",
        status=StrategyProposalStatus.PROPOSED,
    )
    await repo.save_proposal(prop)
    props = await repo.list_proposals_for_company("comp-1")
    assert len(props) == 1

    # 8. Portfolio, Allocation & Improvement
    port = PortfolioItem(
        id="port-1",
        company_id="comp-1",
        title="Core Platform Upgrade",
        reference_id="proj-101",
    )
    await repo.save_portfolio_item(port)
    ports = await repo.list_portfolio_items_for_company("comp-1")
    assert len(ports) == 1

    alloc = ResourceAllocationPlan(
        id="alloc-1",
        company_id="comp-1",
        cycle_id="cycle-1",
        demand_summary="Engineering heavy demand",
    )
    await repo.save_allocation_plan(alloc)
    allocs = await repo.list_allocation_plans_for_company("comp-1")
    assert len(allocs) == 1

    imp = ContinuousImprovementProposal(
        id="imp-1",
        company_id="comp-1",
        title="Automate Retrospectives",
        proposed_change="Trigger retro after each completed initiative",
    )
    await repo.save_improvement_proposal(imp)
    imps = await repo.list_improvement_proposals_for_company("comp-1")
    assert len(imps) == 1

    # 9. Simulation
    sim = StrategySimulation(
        id="sim-1",
        company_id="comp-1",
        title="Scenario X: 50% Token Price Surge",
    )
    await repo.save_simulation(sim)
    sims = await repo.list_simulations_for_company("comp-1")
    assert len(sims) == 1
    assert sims[0].is_authoritative is False
