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
