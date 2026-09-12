"""
Unit tests for TaskDependency domain entity and self-dependency rejection.
"""

import pytest

from src.domain.exceptions import TaskDependencyError
from src.domain.task_dependency import DependencyStatus, DependencyType, TaskDependency


def test_task_dependency_creation() -> None:
    dep = TaskDependency(
        id="dep-1",
        predecessor_task_id="t1",
        successor_task_id="t2",
    )
    assert dep.id == "dep-1"
    assert dep.predecessor_task_id == "t1"
    assert dep.successor_task_id == "t2"
    assert dep.dependency_type == DependencyType.BLOCKING
    assert dep.status == DependencyStatus.ACTIVE


def test_self_dependency_rejected() -> None:
    with pytest.raises(TaskDependencyError, match="cannot depend on itself"):
        TaskDependency(
            id="dep-1",
            predecessor_task_id="t1",
            successor_task_id="t1",
        )


def test_empty_fields_rejected() -> None:
    with pytest.raises(TaskDependencyError, match="ID cannot be empty"):
        TaskDependency(id="", predecessor_task_id="t1", successor_task_id="t2")

    with pytest.raises(TaskDependencyError, match="predecessor_task_id cannot be empty"):
        TaskDependency(id="d1", predecessor_task_id="", successor_task_id="t2")

    with pytest.raises(TaskDependencyError, match="successor_task_id cannot be empty"):
        TaskDependency(id="d1", predecessor_task_id="t1", successor_task_id="")
