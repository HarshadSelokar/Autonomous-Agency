"""
Company Simulation & Scenario Engine Domain Models for Phase 25.

Defines Simulation entity, SimulationSnapshots, Scenarios, Variables, Results,
and SimulationFinancialRecords with strict reality vs simulation isolation.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from src.domain.company import ExecutionEnvironment
from src.domain.exceptions import SimulationProductionMutationError


class SimulationStatus(str, Enum):
    DRAFT = "DRAFT"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


@dataclass
class CompanySimulation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    name: str = ""
    scenario_id: str = ""
    snapshot_id: str = ""
    environment: ExecutionEnvironment = ExecutionEnvironment.SIMULATION
    status: SimulationStatus = SimulationStatus.DRAFT
    owner_id: str = "SYSTEM"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def assert_simulation_safety(self, action_name: str) -> None:
        """Blocks any attempt to execute production mutations inside simulation context."""
        if self.environment != ExecutionEnvironment.SIMULATION:
            raise ValueError(f"Invalid environment '{self.environment.value}' for simulation execution.")
        
        # Production mutation actions strictly prohibited in simulation
        blocked_actions = [
            "CHARGE_CREDIT_CARD",
            "SEND_EXTERNAL_EMAIL",
            "MUTATE_PRODUCTION_DATABASE",
            "EXECUTE_PRODUCTION_DEPLOYMENT",
            "SIGN_REAL_CONTRACT",
            "TRANSFER_REAL_FUNDS",
        ]
        if action_name.upper() in blocked_actions:
            raise SimulationProductionMutationError(self.id, action_name)


@dataclass
class SimulationSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    snapshot_name: str = ""
    snapshot_data: Dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SimulationScenario:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    name: str = ""
    description: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SimulationVariable:
    name: str = ""
    baseline_value: float = 0.0
    simulated_value: float = 0.0
    unit: str = ""
    confidence: float = 0.95


@dataclass
class SimulationResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    simulation_id: str = ""
    company_id: str = ""
    scenario_name: str = ""
    baseline_metrics: Dict[str, Any] = field(default_factory=dict)
    simulated_metrics: Dict[str, Any] = field(default_factory=dict)
    variance_analysis: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.90
    produced_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SimulationFinancialRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    simulation_id: str = ""
    company_id: str = ""
    record_type: str = "SIMULATED_REVENUE"
    amount_cents: int = 0
    currency: str = "USD"
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
