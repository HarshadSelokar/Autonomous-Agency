"""
Unit tests for TaskGraph DAG model, cycle detection, topological sorting, and readiness evaluation.
"""

import pytest

from src.domain.exceptions import TaskCycleError, TaskDependencyError
from src.domain.task import BlockReason, Task, TaskStatus
from src.domain.task_dependency import TaskDependency
from src.domain.task_graph import TaskGraph


def create_task(task_id: str, status: TaskStatus = TaskStatus.PLANNED) -> Task:
    return Task(
        id=task_id,
        plan_id="plan-1",
        title=f"Task {task_id}",
        description=f"Description {task_id}",
        status=status,
    )


def test_linear_graph() -> None:
    graph = TaskGraph()
    t1 = create_task("T1")
    t2 = create_task("T2")
    t3 = create_task("T3")

    graph.add_task(t1)
    graph.add_task(t2)
    graph.add_task(t3)

    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"))
    graph.add_dependency(TaskDependency(id="d2", predecessor_task_id="T2", successor_task_id="T3"))

    topo = [t.id for t in graph.get_topological_sort()]
    assert topo == ["T1", "T2", "T3"]
    assert graph.detect_cycle() is None


def test_diamond_graph() -> None:
    # T1 -> T2, T1 -> T3, T2 -> T4, T3 -> T4
    graph = TaskGraph()
    for tid in ["T1", "T2", "T3", "T4"]:
        graph.add_task(create_task(tid))

    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"))
    graph.add_dependency(TaskDependency(id="d2", predecessor_task_id="T1", successor_task_id="T3"))
    graph.add_dependency(TaskDependency(id="d3", predecessor_task_id="T2", successor_task_id="T4"))
    graph.add_dependency(TaskDependency(id="d4", predecessor_task_id="T3", successor_task_id="T4"))

    topo = [t.id for t in graph.get_topological_sort()]
    assert topo[0] == "T1"
    assert topo[-1] == "T4"
    assert set(topo[1:3]) == {"T2", "T3"}


def test_direct_cycle_rejected() -> None:
    graph = TaskGraph()
    graph.add_task(create_task("T1"))
    graph.add_task(create_task("T2"))

    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"))
    with pytest.raises(TaskCycleError, match="creates a dependency cycle"):
        graph.add_dependency(
            TaskDependency(id="d2", predecessor_task_id="T2", successor_task_id="T1")
        )


def test_long_cycle_rejected() -> None:
    # T1 -> T2 -> T3 -> T4 -> T5 -> T1
    graph = TaskGraph()
    nodes = ["T1", "T2", "T3", "T4", "T5"]
    for tid in nodes:
        graph.add_task(create_task(tid))

    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"))
    graph.add_dependency(TaskDependency(id="d2", predecessor_task_id="T2", successor_task_id="T3"))
    graph.add_dependency(TaskDependency(id="d3", predecessor_task_id="T3", successor_task_id="T4"))
    graph.add_dependency(TaskDependency(id="d4", predecessor_task_id="T4", successor_task_id="T5"))

    with pytest.raises(TaskCycleError, match="creates a dependency cycle"):
        graph.add_dependency(
            TaskDependency(id="d5", predecessor_task_id="T5", successor_task_id="T1")
        )


def test_self_dependency_rejected() -> None:
    graph = TaskGraph()
    graph.add_task(create_task("T1"))
    with pytest.raises(TaskDependencyError, match="cannot depend on itself"):
        graph.add_dependency(
            TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T1")
        )


def test_readiness_evaluation() -> None:
    graph = TaskGraph()
    t1 = create_task("T1", status=TaskStatus.IN_PROGRESS)
    t2 = create_task("T2", status=TaskStatus.PLANNED)

    graph.add_task(t1)
    graph.add_task(t2)
    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"))

    is_ready, reasons = graph.evaluate_readiness("T2")
    assert not is_ready
    assert BlockReason.DEPENDENCY_INCOMPLETE in reasons

    # Complete T1
    t1.status = TaskStatus.COMPLETED
    is_ready, reasons = graph.evaluate_readiness("T2")
    assert is_ready
    assert reasons == []

    # Fail T1
    t1.status = TaskStatus.FAILED
    is_ready, reasons = graph.evaluate_readiness("T2")
    assert not is_ready
    assert BlockReason.DEPENDENCY_FAILED in reasons
