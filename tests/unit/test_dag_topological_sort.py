"""
Comprehensive unit tests for DAG structure, topological sorting, and parallel branch execution.
"""

from src.domain.task import Task, TaskStatus
from src.domain.task_dependency import TaskDependency
from src.domain.task_graph import TaskGraph


def test_complex_dag_topological_ordering() -> None:
    # Build 6-node DAG:
    # T1 -> T2 -> (T3, T4) -> T5 -> T6
    graph = TaskGraph()
    tasks = {
        f"T{i}": Task(id=f"T{i}", plan_id="p1", title=f"T{i}", description=f"D{i}")
        for i in range(1, 7)
    }
    for t in tasks.values():
        graph.add_task(t)

    deps = [
        TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"),
        TaskDependency(id="d2", predecessor_task_id="T2", successor_task_id="T3"),
        TaskDependency(id="d3", predecessor_task_id="T2", successor_task_id="T4"),
        TaskDependency(id="d4", predecessor_task_id="T3", successor_task_id="T5"),
        TaskDependency(id="d5", predecessor_task_id="T4", successor_task_id="T5"),
        TaskDependency(id="d6", predecessor_task_id="T5", successor_task_id="T6"),
    ]
    for d in deps:
        graph.add_dependency(d)

    topo = [t.id for t in graph.get_topological_sort()]
    assert topo[0] == "T1"
    assert topo[1] == "T2"
    assert set(topo[2:4]) == {"T3", "T4"}
    assert topo[4] == "T5"
    assert topo[5] == "T6"


def test_parallel_branch_readiness_evaluation() -> None:
    # T3 and T4 depend on T2. Both T3 and T4 must complete before T5 is READY.
    graph = TaskGraph()
    t2 = Task(id="T2", plan_id="p1", title="T2", description="D2", status=TaskStatus.COMPLETED)
    t3 = Task(id="T3", plan_id="p1", title="T3", description="D3", status=TaskStatus.IN_PROGRESS)
    t4 = Task(id="T4", plan_id="p1", title="T4", description="D4", status=TaskStatus.COMPLETED)
    t5 = Task(id="T5", plan_id="p1", title="T5", description="D5", status=TaskStatus.PLANNED)

    for t in [t2, t3, t4, t5]:
        graph.add_task(t)

    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="T3", successor_task_id="T5"))
    graph.add_dependency(TaskDependency(id="d2", predecessor_task_id="T4", successor_task_id="T5"))

    # Because T3 is IN_PROGRESS, T5 is BLOCKED
    is_ready, reasons = graph.evaluate_readiness("T5")
    assert not is_ready

    # Complete T3 -> T5 becomes READY
    t3.status = TaskStatus.COMPLETED
    is_ready, reasons = graph.evaluate_readiness("T5")
    assert is_ready
    assert reasons == []
