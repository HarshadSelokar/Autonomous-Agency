"""
Unit tests for Budget domain entities and economic reservation logic (Phase 35).
"""

import pytest
from src.domain.budget import Budget, BudgetType
from src.domain.exceptions import ResourceBudgetExceededError


def test_budget_reservation_and_commit():
    budget = Budget(
        id="b-1",
        tenant_id="t-1",
        allocated_amount=50.0,
    )
    assert budget.remaining_amount() == 50.0

    # Reserve $10
    budget.reserve(10.0)
    assert budget.reserved_amount == 10.0
    assert budget.remaining_amount() == 40.0

    # Commit $10 reservation with $8 actual usage
    budget.commit_reservation(reserved_amount=10.0, actual_used=8.0)
    assert budget.reserved_amount == 0.0
    assert budget.used_amount == 8.0
    assert budget.remaining_amount() == 42.0


def test_budget_exceeded_error():
    budget = Budget(
        id="b-2",
        tenant_id="t-1",
        allocated_amount=10.0,
    )

    with pytest.raises(ResourceBudgetExceededError):
        budget.reserve(15.0)
