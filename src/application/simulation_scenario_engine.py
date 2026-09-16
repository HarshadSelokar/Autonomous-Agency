"""
Simulation Scenario Calculation Engine for Phase 25.

Evaluates simulation scenarios against isolated baseline snapshots, computes variance analytics,
and produces comparative SimulationResults without mutating production state.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.simulation import (
    CompanySimulation,
    SimulationScenario,
    SimulationSnapshot,
    SimulationResult,
    SimulationFinancialRecord,
    SimulationStatus,
)
from src.domain.events import SimulationCompletedEvent, SimulationResultProducedEvent
from src.domain.repository import MultiCompanyRepositoryInterface


class SimulationScenarioEngine:
    """Computes simulated company outcomes and variance analysis."""

    def __init__(self, repository: MultiCompanyRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def run_simulation(self, simulation_id: str) -> SimulationResult:
        sim = await self.repository.get_simulation_by_id(simulation_id)
        if not sim:
            raise ValueError(f"Simulation '{simulation_id}' not found.")

        # Enforce structural safety assertion
        sim.assert_simulation_safety("COMPUTE_SCENARIO_OUTCOMES")

        snapshot = await self.repository.get_simulation_snapshot_by_id(sim.snapshot_id)
        if not snapshot:
            raise ValueError(f"Simulation snapshot '{sim.snapshot_id}' not found.")

        scenario = await self.repository.get_simulation_scenario_by_id(sim.scenario_id)
        if not scenario:
            raise ValueError(f"Simulation scenario '{sim.scenario_id}' not found.")

        baseline = snapshot.snapshot_data
        vars_dict = scenario.variables

        # 1. Compute Simulated Metrics
        base_revenue = float(baseline.get("revenue_cents", 10000000))
        base_expenses = float(baseline.get("expenses_cents", 5000000))
        base_headcount = float(baseline.get("headcount", 10))
        base_customers = float(baseline.get("customers", 25))

        # Scenario Multipliers
        headcount_mult = float(vars_dict.get("headcount_multiplier", 1.0))
        marketing_boost_pct = float(vars_dict.get("marketing_boost_pct", 0.0))
        price_mult = float(vars_dict.get("price_multiplier", 1.0))
        churn_delta_pct = float(vars_dict.get("churn_delta_pct", 0.0))

        sim_headcount = round(base_headcount * headcount_mult)
        sim_customers = round(base_customers * (1.0 + (marketing_boost_pct / 100.0) - (churn_delta_pct / 100.0)))
        sim_revenue = round(base_revenue * (sim_customers / max(1.0, base_customers)) * price_mult)
        sim_expenses = round(base_expenses * headcount_mult * 1.1)

        simulated_metrics = {
            "revenue_cents": int(sim_revenue),
            "expenses_cents": int(sim_expenses),
            "net_profit_cents": int(sim_revenue - sim_expenses),
            "headcount": sim_headcount,
            "customers": sim_customers,
        }

        baseline_metrics = {
            "revenue_cents": int(base_revenue),
            "expenses_cents": int(base_expenses),
            "net_profit_cents": int(base_revenue - base_expenses),
            "headcount": int(base_headcount),
            "customers": int(base_customers),
        }

        # 2. Compute Variance Analysis
        variance_analysis = {
            "revenue_delta_pct": round(((sim_revenue - base_revenue) / base_revenue) * 100.0, 2),
            "expenses_delta_pct": round(((sim_expenses - base_expenses) / base_expenses) * 100.0, 2),
            "net_profit_delta_cents": int((sim_revenue - sim_expenses) - (base_revenue - base_expenses)),
            "headcount_delta": int(sim_headcount - base_headcount),
            "customers_delta": int(sim_customers - base_customers),
        }

        # 3. Save Isolated Simulated Financial Record
        sim_fin_record = SimulationFinancialRecord(
            id=str(uuid.uuid4()),
            simulation_id=sim.id,
            company_id=sim.company_id,
            record_type="SIMULATED_PROJECTED_REVENUE",
            amount_cents=int(sim_revenue),
            currency="USD",
            description=f"Simulated Revenue projection for Scenario '{scenario.name}'",
            created_at=datetime.now(UTC),
        )
        await self.repository.save_simulation_financial_record(sim_fin_record)

        # 4. Save Simulation Result
        result = SimulationResult(
            id=str(uuid.uuid4()),
            simulation_id=sim.id,
            company_id=sim.company_id,
            scenario_name=scenario.name,
            baseline_metrics=baseline_metrics,
            simulated_metrics=simulated_metrics,
            variance_analysis=variance_analysis,
            confidence_score=0.92,
            produced_at=datetime.now(UTC),
        )
        saved_result = await self.repository.save_simulation_result(result)

        # 5. Complete Simulation Lifecycle
        sim.status = SimulationStatus.COMPLETED
        sim.updated_at = datetime.now(UTC)
        await self.repository.save_simulation(sim)

        self._publish_event(SimulationCompletedEvent(simulation_id=sim.id, company_id=sim.company_id, result_id=saved_result.id))
        self._publish_event(
            SimulationResultProducedEvent(
                result_id=saved_result.id,
                simulation_id=sim.id,
                company_id=sim.company_id,
                scenario_name=scenario.name,
            )
        )

        return saved_result
