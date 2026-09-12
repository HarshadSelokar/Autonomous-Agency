"""
Unit tests for Task domain entity and TaskStatus state machine transitions.
"""

import pytest

from src.domain.exceptions import InvalidStateTransitionError, TaskValidationError
from src.domain.task import Task, TaskStatus


def test_task_creation_and_validation() -> None:
    task = Task(
        id="task-1",
        plan_id="plan-1",
        title="Test Task",
        description="Test Task Description",
        priority="high",
    )
    assert task.id == "task-1"
    assert task.status == TaskStatus.CREATED
    assert task.priority == "high"
    assert task.retry_count == 0
    assert task.max_retries == 3


def test_task_invalid_fields() -> None:
    with pytest.raises(TaskValidationError, match="Task ID cannot be empty"):
        Task(id="", plan_id="plan-1", title="T", description="D")

    with pytest.raises(TaskValidationError, match="Invalid priority"):
        Task(id="t1", plan_id="p1", title="T", description="D", priority="ultra")


def test_task_valid_state_transitions() -> None:
    task = Task(id="t1", plan_id="p1", title="T", description="D")
    assert task.status == TaskStatus.CREATED

    task.transition_to(TaskStatus.PLANNED)
    assert task.status == TaskStatus.PLANNED

    task.transition_to(TaskStatus.READY)
    assert task.status == TaskStatus.READY

    task.transition_to(TaskStatus.ASSIGNED)
    assert task.status == TaskStatus.ASSIGNED

    task.transition_to(TaskStatus.IN_PROGRESS)
    assert task.status == TaskStatus.IN_PROGRESS

    task.transition_to(TaskStatus.REVIEW)
    assert task.status == TaskStatus.REVIEW

    task.transition_to(TaskStatus.APPROVED)
    assert task.status == TaskStatus.APPROVED

    task.transition_to(TaskStatus.COMPLETED)
    assert task.status == TaskStatus.COMPLETED


def test_task_rework_flow() -> None:
    task = Task(id="t1", plan_id="p1", title="T", description="D", status=TaskStatus.REVIEW)
    task.transition_to(TaskStatus.REWORK)
    assert task.status == TaskStatus.REWORK

    task.transition_to(TaskStatus.IN_PROGRESS)
    assert task.status == TaskStatus.IN_PROGRESS


def test_task_invalid_state_transition() -> None:
    task = Task(id="t1", plan_id="p1", title="T", description="D")
    with pytest.raises(InvalidStateTransitionError):
        task.transition_to(TaskStatus.COMPLETED)


def test_task_self_parenting_rejected() -> None:
    with pytest.raises(TaskValidationError, match="cannot be its own parent"):
        Task(id="t1", plan_id="p1", parent_task_id="t1", title="T", description="D")

    task = Task(id="t1", plan_id="p1", title="T", description="D")
    with pytest.raises(TaskValidationError, match="cannot be set as its own parent"):
        task.set_parent("t1")


def test_task_circular_parent_hierarchy_rejected() -> None:
    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1")
    t2 = Task(id="t2", plan_id="p1", parent_task_id="t1", title="T2", description="D2")
    t3 = Task(id="t3", plan_id="p1", parent_task_id="t2", title="T3", description="D3")

    task_map = {"t1": t1, "t2": t2, "t3": t3}

    # Attempting to make t1 child of t3 creates cycle t1 -> t3 -> t2 -> t1
    with pytest.raises(TaskValidationError, match="circular parent-child hierarchy"):
        t1.set_parent("t3", task_map=task_map)


def test_task_valid_parent_hierarchy() -> None:
    parent = Task(id="parent-1", plan_id="p1", title="Parent Task", description="Parent Desc")
    child = Task(
        id="child-1",
        plan_id="p1",
        parent_task_id="parent-1",
        title="Child Task",
        description="Child Desc",
    )

    assert child.parent_task_id == "parent-1"
    task_map = {"parent-1": parent, "child-1": child}
    child.set_parent(None, task_map=task_map)
    assert child.parent_task_id is None
