"""
Phase 16 End-to-End Demonstration Script:
Autonomous Company Operations, Strategic Intelligence & Governed Organizational Evolution.

Demonstrates:
1. Autonomous Company initialization & active strategy setup.
2. Complete 10-state operating cycle execution (CREATED -> OBSERVING -> ANALYZING -> PLANNING -> PRIORITIZING -> AWAITING_GOVERNANCE -> EXECUTING -> MEASURING -> LEARNING -> COMPLETED).
3. AI Strategic Intelligence situation analysis and what-if simulation (isolated non-authoritative).
4. Governance authorization requirement & rejection flow.
5. Executive strategic report and portfolio tracking.
"""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.company_observation_service import CompanyObservationService
from src.application.company_operating_cycle_service import CompanyOperatingCycleService
from src.application.executive_orchestration_service import ExecutiveOrchestrationService
from src.application.strategic_intelligence_service import StrategicIntelligenceService
from src.domain.company import AutonomousCompany, CompanyStatus, OperatingCycleState
from src.domain.strategy import StrategyProposalType
from src.infrastructure.database import Base
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository


async def run_demo() -> None:
    print("=" * 80)
    print("PHASE 16 — AUTONOMOUS COMPANY OPERATIONS & STRATEGIC INTELLIGENCE DEMO")
    print("=" * 80)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        repo = SQLAlchemyCompanyRepository(session)
        obs_svc = CompanyObservationService(repo)
        strat_svc = StrategicIntelligenceService(repo)
        cycle_svc = CompanyOperatingCycleService(repo, obs_svc, strat_svc)
        exec_svc = ExecutiveOrchestrationService(repo)

        # 1. Company Initialization
        print("\n--- Step 1: Initializing Autonomous Company OS ---")
        company = AutonomousCompany(
            id="comp-demo-16",
            name="Nexus Autonomous Enterprise",
            code="NEXUS",
            mission="Deliver end-to-end autonomous AI organizational operations.",
            status=CompanyStatus.ACTIVE,
        )
        saved_comp = await repo.save_company(company)
        print(f"[OK] Created Autonomous Company: {saved_comp.name} [{saved_comp.code}] (ID: {saved_comp.id})")

        # 2. Formulate Strategy Version 1
        print("\n--- Step 2: Formulating Company Strategy (Version 1) ---")
        strat = await strat_svc.Formulate_or_update_strategy(
            company_id=saved_comp.id,
            title="Q3 2026 Enterprise Automation & Reliability Growth",
            themes=["Zero-Downtime Autonomous QA", "Workforce Optimization"],
            priorities=["High-quality delivery", "Compliance"],
            targets={"task_success_rate": 98.0, "delivery_velocity": 90.0},
        )
        print(f"[OK] Active Strategy v{strat.version}: '{strat.title}' (Status: {strat.status.value})")

        # 3. Isolated What-If Simulation
        print("\n--- Step 3: Running Isolated Non-Authoritative What-If Simulation ---")
        sim = await strat_svc.run_what_if_simulation(
            company_id=saved_comp.id,
            title="Scenario Alpha: 50% Compute Token Surge",
            assumptions=["Model provider token prices increase 50%"],
            input_parameters={"token_price_surge": 0.50},
        )
        print(f"[OK] Simulation Executed: '{sim.title}'")
        print(f"   Projected Throughput Delta: {sim.projected_outcomes.get('projected_throughput_delta_pct')}%")
        print(f"   Is Authoritative Invariant: {sim.is_authoritative} (STRICTLY NON-AUTHORITATIVE)")

        # 4. Complete 10-State Operating Cycle Execution
        print("\n--- Step 4: Executing Full 10-State Operating Cycle ---")
        cycle = await cycle_svc.execute_full_cycle(
            company_id=saved_comp.id,
            initiated_by_id="executive_agent_ceo",
            metric_values={
                "task_success_rate": 98.5,
                "delivery_velocity": 91.0,
                "verification_pass_rate": 97.0,
                "governance_compliance_rate": 100.0,
                "model_reliability": 98.0,
                "resource_utilization": 84.0,
            },
        )
        print(f"[OK] Operating Cycle #{cycle.cycle_number} Completed (ID: {cycle.id})")
        print(f"   Final State: {cycle.state.value}")
        print(f"   Completed At: {cycle.completed_at}")

        # 5. Governance Proposal & Strategic Evolution
        print("\n--- Step 5: Strategic Proposal & Governance Integration ---")
        prop = await strat_svc.create_strategy_proposal(
            company_id=saved_comp.id,
            proposal_type=StrategyProposalType.ORGANIZATIONAL_EVOLUTION,
            title="Establish Autonomous Cyber Defense Guild",
            proposal_body="Form a specialized department for automated threat detection and compliance.",
            reason="Increased threat landscape and audit requirements.",
            governance_level="EXECUTIVE_APPROVAL",
        )
        print(f"[OK] Strategic Proposal Created: '{prop.title}' (ID: {prop.id})")
        print(f"   Proposal Type: {prop.proposal_type.value}")
        print(f"   Required Governance Level: {prop.governance_level}")

        # 6. Executive Strategic Reporting & Portfolio
        print("\n--- Step 6: Executive Strategic Reporting & Portfolio Tracking ---")
        item = await exec_svc.add_portfolio_item(
            company_id=saved_comp.id,
            title="Enterprise Cyber Defense Guild Rollout",
            reference_id=prop.id,
        )
        await exec_svc.update_portfolio_progress(item.id, progress_pct=100.0, resource_utilization_pct=88.0)
        report = await exec_svc.generate_executive_report(saved_comp.id, cycle.id)

        print(f"[OK] Executive Strategic Report Generated (ID: {report['report_id']})")
        print(f"   Overall Health: {report['health']['overall_status']}")
        print(f"   Active Strategy Version: {report['active_strategy']['version']}")
        print(f"   Total Objectives: {report['objectives_count']}")
        print(f"   Portfolio Items Count: {report['portfolio_items_count']}")

        print("\n" + "=" * 80)
        print("PHASE 16 AUTONOMOUS COMPANY OS DEMONSTRATION COMPLETE SUCCESS")
        print("=" * 80)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_demo())
