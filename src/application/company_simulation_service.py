"""
Company Simulation Management Application Service for Phase 25.

Orchestrates point-in-time snapshot creation, simulation initialization, and lifecycle management
with strict simulation safety enforcement.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.company import ExecutionEnvironment
from src.domain.simulation import (
    CompanySimulation,
    SimulationSnapshot,
    SimulationScenario,
    SimulationStatus,
)
from src.domain.events import (
    SimulationCreatedEvent,
    SimulationStartedEvent,
    SimulationCompletedEvent,
)
from src.domain.repository import MultiCompanyRepositoryInterface


class CompanySimulationService:
    """Manages company simulation environments, snapshots, and scenarios."""

    def __init__(self, repository: MultiCompanyRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_snapshot(
        self,
        company_id: str,
        snapshot_name: str,
        baseline_metrics: Dict[str, Any],
    ) -> SimulationSnapshot:
        snapshot = SimulationSnapshot(
            id=str(uuid.uuid4()),
            company_id=company_id,
            snapshot_name=snapshot_name,
            snapshot_data=baseline_metrics,
            recorded_at=datetime.now(UTC),
        )
        return await self.repository.save_simulation_snapshot(snapshot)

    async def create_scenario(
        self,
        company_id: str,
        name: str,
        description: str,
        variables: Dict[str, Any],
    ) -> SimulationScenario:
        scenario = SimulationScenario(
            id=str(uuid.uuid4()),
            company_id=company_id,
            name=name,
            description=description,
            variables=variables,
            created_at=datetime.now(UTC),
        )
        return await self.repository.save_simulation_scenario(scenario)

    async def create_simulation(
        self,
        company_id: str,
        name: str,
        scenario_id: str,
        snapshot_id: str,
        owner_id: str = "SYSTEM",
    ) -> CompanySimulation:
        snapshot = await self.repository.get_simulation_snapshot_by_id(snapshot_id)
        if not snapshot:
            raise ValueError(f"Simulation snapshot '{snapshot_id}' not found.")

        scenario = await self.repository.get_simulation_scenario_by_id(scenario_id)
        if not scenario:
            raise ValueError(f"Simulation scenario '{scenario_id}' not found.")

        simulation = CompanySimulation(
            id=str(uuid.uuid4()),
            company_id=company_id,
            name=name,
            scenario_id=scenario_id,
            snapshot_id=snapshot_id,
            environment=ExecutionEnvironment.SIMULATION,
            status=SimulationStatus.READY,
            owner_id=owner_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        saved = await self.repository.save_simulation(simulation)
        self._publish_event(SimulationCreatedEvent(simulation_id=saved.id, company_id=company_id, scenario_id=scenario_id))
        return saved

    async def start_simulation(self, simulation_id: str) -> CompanySimulation:
        sim = await self.repository.get_simulation_by_id(simulation_id)
        if not sim:
            raise ValueError(f"Simulation '{simulation_id}' not found.")

        sim.status = SimulationStatus.RUNNING
        sim.updated_at = datetime.now(UTC)
        saved = await self.repository.save_simulation(sim)
        self._publish_event(SimulationStartedEvent(simulation_id=saved.id, company_id=saved.company_id))
        return saved
