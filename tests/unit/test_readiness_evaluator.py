"""
Unit tests for ReadinessEvaluator service.
"""

from src.application.readiness_evaluator import ReadinessEvaluator
from src.domain.task import BlockReason, Task, TaskStatus
from src.domain.task_dependency import TaskDependency
from src.domain.task_graph import TaskGraph


def test_readiness_evaluator_standalone_task() -> None:
    graph = TaskGraph()
    task = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.PLANNED)
    graph.add_task(task)

    evaluator = ReadinessEvaluator()
    is_ready, reasons = evaluator.evaluate_task(task, graph)

    assert is_ready
    assert reasons == []

    changed = evaluator.update_task_readiness(task, graph)
    assert changed
    assert task.status == TaskStatus.READY


def test_readiness_evaluator_blocked_by_predecessor() -> None:
    graph = TaskGraph()
    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.IN_PROGRESS)
    t2 = Task(id="t2", plan_id="p1", title="T2", description="D2", status=TaskStatus.PLANNED)

    graph.add_task(t1)
    graph.add_task(t2)
    graph.add_dependency(
        TaskDependency(id="dep1", predecessor_task_id="t1", successor_task_id="t2")
    )

    evaluator = ReadinessEvaluator()
    is_ready, reasons = evaluator.evaluate_task(t2, graph)
    assert not is_ready
    assert BlockReason.DEPENDENCY_INCOMPLETE in reasons

    evaluator.update_task_readiness(t2, graph)
    assert t2.status == TaskStatus.BLOCKED
    assert BlockReason.DEPENDENCY_INCOMPLETE in t2.block_reasons

    # Complete predecessor t1
    t1.status = TaskStatus.COMPLETED
    evaluator.update_task_readiness(t2, graph)
    assert t2.status == TaskStatus.READY
    assert t2.block_reasons == []


def test_readiness_evaluator_predecessor_failed() -> None:
    graph = TaskGraph()
    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.FAILED)
    t2 = Task(id="t2", plan_id="p1", title="T2", description="D2", status=TaskStatus.PLANNED)

    graph.add_task(t1)
    graph.add_task(t2)
    graph.add_dependency(
        TaskDependency(id="dep1", predecessor_task_id="t1", successor_task_id="t2")
    )

    evaluator = ReadinessEvaluator()
    evaluator.update_task_readiness(t2, graph)
    assert t2.status == TaskStatus.BLOCKED
    assert BlockReason.DEPENDENCY_FAILED in t2.block_reasons
