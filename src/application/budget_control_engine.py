"""
Budget Control Engine for Phase 23.

Provides deterministic budget allocation, utilization tracking, and threshold enforcement.
"""

from typing import Dict, List, Optional

from src.domain.business import Budget, BudgetAllocation
from src.domain.exceptions import BudgetExceededError


class BudgetControlEngine:
    """Evaluates budget allocations and enforces remaining budget invariants."""

    def check_and_consume(self, budget: Budget, amount_cents: int, category: Optional[str] = None) -> None:
        """
        Validates whether expenditure fits within available budget.
        Consumes budget deterministically or raises BudgetExceededError.
        """
        if budget.status != "ACTIVE":
            raise BudgetExceededError(budget.id, amount_cents, 0)

        # Check total remaining
        if amount_cents > budget.remaining_cents:
            raise BudgetExceededError(budget.id, amount_cents, budget.remaining_cents)

        # Check category allocation if specified
        if category and budget.allocations:
            alloc = next((a for a in budget.allocations if a.category.lower() == category.lower()), None)
            if alloc:
                if amount_cents > alloc.remaining_cents:
                    raise BudgetExceededError(f"{budget.id}:{category}", amount_cents, alloc.remaining_cents)
                alloc.consumed_cents += amount_cents

        # Consume main budget
        budget.consume(amount_cents)

    def calculate_utilization_pct(self, budget: Budget) -> float:
        if budget.allocated_cents <= 0:
            return 0.0
        return round((budget.consumed_cents / budget.allocated_cents) * 100.0, 2)
