"""
Resource Quotas, Budgets, and Cost Governance Domain Entities (Phase 35).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ResourceBudgetExceededError, QuotaExceededError


class BudgetType(str, Enum):
    TOKEN = "TOKEN"
    COST = "COST"
    TOOL_CALL = "TOOL_CALL"
    COMPUTE_TIME = "COMPUTE_TIME"


@dataclass
class Budget:
    id: str
    tenant_id: str
    project_id: str | None = None
    budget_type: BudgetType = BudgetType.COST
    allocated_amount: float = 0.0
    used_amount: float = 0.0
    reserved_amount: float = 0.0
    currency: str = "USD"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def remaining_amount(self) -> float:
        return self.allocated_amount - (self.used_amount + self.reserved_amount)

    def can_reserve(self, amount: float) -> bool:
        return self.remaining_amount() >= amount

    def reserve(self, amount: float) -> None:
        if not self.can_reserve(amount):
            raise ResourceBudgetExceededError(
                tenant_id=self.tenant_id,
                project_id=self.project_id or "GLOBAL",
                budget_type=self.budget_type.value,
                current_usage=self.used_amount + self.reserved_amount + amount,
                budget_limit=self.allocated_amount,
            )
        self.reserved_amount += amount
        self.updated_at = datetime.now(UTC)

    def commit_reservation(self, reserved_amount: float, actual_used: float) -> None:
        self.reserved_amount = max(0.0, self.reserved_amount - reserved_amount)
        self.used_amount += actual_used
        self.updated_at = datetime.now(UTC)

    def release_reservation(self, amount: float) -> None:
        self.reserved_amount = max(0.0, self.reserved_amount - amount)
        self.updated_at = datetime.now(UTC)


@dataclass
class CostRecord:
    id: str
    tenant_id: str
    project_id: str | None
    task_id: str | None
    agent_id: str | None
    model_name: str
    tokens_prompt: int
    tokens_completion: int
    estimated_cost: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
