"""
Unit tests for Recovery Domain Model (Phase 10).
"""

from src.domain.recovery import (
    FailureBudget,
    FailureCategory,
    FailureRecord,
    RecoveryStrategy,
)


def test_failure_record_creation():
    record = FailureRecord(
        failure_id="f1",
        task_id="t1",
        verification_id="v1",
        category=FailureCategory.TEST_FAILURE,
        severity="HIGH",
        summary="3 tests failed in module X",
        retryable=True,
        recommended_strategy=RecoveryStrategy.REWORK,
    )
    assert record.failure_id == "f1"
    assert record.category == FailureCategory.TEST_FAILURE
    assert record.recommended_strategy == RecoveryStrategy.REWORK


def test_failure_budget_limits():
    budget = FailureBudget(max_retries=3, max_reworks=2, max_reassignments=1)

    assert not budget.is_retry_exhausted(0)
    assert not budget.is_retry_exhausted(2)
    assert budget.is_retry_exhausted(3)

    assert not budget.is_rework_exhausted(1)
    assert budget.is_rework_exhausted(2)

    assert not budget.is_reassignment_exhausted(0)
    assert budget.is_reassignment_exhausted(1)
