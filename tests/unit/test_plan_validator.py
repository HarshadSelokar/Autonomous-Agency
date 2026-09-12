"""
Unit tests for PlanValidator service.
"""

import pytest

from src.application.plan_validator import PlanValidator
from src.domain.exceptions import PlanValidationError
from src.domain.plan import Plan, PlanStatus
from src.domain.work_item import WorkItem


def test_plan_validator_valid_plan() -> None:
    validator = PlanValidator()
    wi1 = WorkItem(
        id="wi_1",
        plan_id="p1",
        title="Task 1",
        description="Desc 1",
        required_capabilities=["python"],
    )
    wi2 = WorkItem(
        id="wi_2",
        plan_id="p1",
        title="Task 2",
        description="Desc 2",
        required_capabilities=["postgresql"],
    )
    plan = Plan(
        id="p1",
        objective_id="obj1",
        manager_id="mgr1",
        work_items=[wi1, wi2],
        status=PlanStatus.PROPOSED,
    )

    # Should not raise exception
    validator.validate_proposed_plan(plan)


def test_plan_validator_empty_work_items_fails() -> None:
    validator = PlanValidator()
    plan = Plan(id="p1", objective_id="obj1", manager_id="mgr1", work_items=[])

    with pytest.raises(PlanValidationError) as exc:
        validator.validate_proposed_plan(plan)

    assert "contain at least one work item" in str(exc.value)


def test_plan_validator_duplicate_work_item_id_fails() -> None:
    validator = PlanValidator()
    wi1 = WorkItem(
        id="wi_1", plan_id="p1", title="Task 1", description="D1", required_capabilities=["python"]
    )
    wi2 = WorkItem(
        id="wi_1", plan_id="p1", title="Task 2", description="D2", required_capabilities=["sql"]
    )
    plan = Plan(id="p1", objective_id="obj1", manager_id="mgr1", work_items=[wi1, wi2])

    with pytest.raises(PlanValidationError) as exc:
        validator.validate_proposed_plan(plan)

    assert "Duplicate work item ID 'wi_1'" in str(exc.value)


def test_plan_validator_missing_capabilities_fails() -> None:
    validator = PlanValidator()
    wi = WorkItem(
        id="wi_1", plan_id="p1", title="Task 1", description="D1", required_capabilities=[]
    )
    plan = Plan(id="p1", objective_id="obj1", manager_id="mgr1", work_items=[wi])

    with pytest.raises(PlanValidationError) as exc:
        validator.validate_proposed_plan(plan)

    assert "must specify at least one required capability" in str(exc.value)
