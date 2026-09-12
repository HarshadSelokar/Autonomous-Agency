"""
Failure-Injection Test Suite for Task & Dependency Engine.
Covers 15 failure modes to ensure resilience and deterministic state integrity.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dependency_graph_service import DependencyGraphService
from src.application.readiness_evaluator import ReadinessEvaluator
from src.application.task_claim_service import TaskClaimService
from src.application.task_execution_service import TaskExecutionService
from src.application.task_lifecycle_service import TaskLifecycleService
from src.application.task_scheduler_service import TaskSchedulerService
from src.domain.exceptions import (
    InvalidStateTransitionError,
    TaskClaimError,
    TaskCycleError,
    TaskDependencyError,
    TaskValidationError,
)
from src.domain.task import BlockReason, Task, TaskStatus
from src.domain.task_dependency import TaskDependency
from src.domain.task_graph import TaskGraph


# 1. Database failure during task persistence
def test_fm01_database_failure_during_persistence() -> None:
    repo = MagicMock()
    repo.save.side_effect = RuntimeError("Database connection lost")
    task = Task(id="t1", plan_id="p1", title="T1", description="D1")
    with pytest.raises(RuntimeError, match="Database connection lost"):
        repo.save(task)


# 2. Dependency insertion failure
@pytest.mark.asyncio
async def test_fm02_dependency_insertion_failure() -> None:
    task_repo = MagicMock()
    dep_repo = MagicMock()
    dep_repo.save.side_effect = RuntimeError("Foreign key constraint violation")

    service = DependencyGraphService(task_repo, dep_repo)
    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1")
    t2 = Task(id="t2", plan_id="p1", title="T2", description="D2")
    task_repo.get_by_id.side_effect = lambda tid: t1 if tid == "t1" else t2
    task_repo.get_by_plan_id.return_value = [t1, t2]
    dep_repo.get_by_plan_id.return_value = []

    dep = TaskDependency(id="d1", predecessor_task_id="t1", successor_task_id="t2")
    with pytest.raises(RuntimeError, match="Foreign key constraint violation"):
        await service.add_dependency(dep)


# 3. Cycle detection failure path
def test_fm03_cycle_detection_failure_path() -> None:
    graph = TaskGraph()
    graph.add_task(Task(id="T1", plan_id="p1", title="T1", description="D1"))
    graph.add_task(Task(id="T2", plan_id="p1", title="T2", description="D2"))
    graph.add_task(Task(id="T3", plan_id="p1", title="T3", description="D3"))

    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"))
    graph.add_dependency(TaskDependency(id="d2", predecessor_task_id="T2", successor_task_id="T3"))

    with pytest.raises(TaskCycleError, match="creates a dependency cycle"):
        graph.add_dependency(
            TaskDependency(id="d3", predecessor_task_id="T3", successor_task_id="T1")
        )


# 4. Employee unavailable
@pytest.mark.asyncio
async def test_fm04_employee_unavailable() -> None:
    task_repo = MagicMock()
    claim_service = MagicMock()
    exec_service = AsyncMock()
    emp_selector = MagicMock()
    emp_repo = AsyncMock()

    emp_repo.list_all.return_value = []
    emp_selector.find_eligible_employees.return_value = []

    scheduler = TaskSchedulerService(
        task_repository=task_repo,
        claim_service=claim_service,
        execution_service=exec_service,
        employee_selector=emp_selector,
        employee_repository=emp_repo,
    )

    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)
    task_repo.get_by_status.return_value = [t]
    claim_service.claim_task.return_value = t

    executed = await scheduler.schedule_next_task()
    assert executed is not None
    exec_service.execute_task.assert_awaited_once()
    call_kwargs = exec_service.execute_task.await_args.kwargs
    assert call_kwargs["employee_id"] == "unassigned-emp"
    assert call_kwargs["task"].id == "t1"


# 5. Employee becomes unavailable after selection
@pytest.mark.asyncio
async def test_fm05_employee_becomes_unavailable_after_selection() -> None:
    task_repo = MagicMock()
    emp_service = AsyncMock()
    emp_service.execute_work.side_effect = RuntimeError("Employee is suspended or inactive")

    exec_service = TaskExecutionService(task_repository=task_repo, employee_service=emp_service)
    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)

    result = await exec_service.execute_task(t, employee_id="emp-1", assignment_id="asgn-1")
    assert result.status == TaskStatus.FAILED
    assert "suspended or inactive" in result.metadata["last_execution_error"]


# 6. Agent Runtime timeout
@pytest.mark.asyncio
async def test_fm06_agent_runtime_timeout() -> None:
    task_repo = MagicMock()
    emp_service = AsyncMock()
    emp_service.execute_work.side_effect = TimeoutError("Agent execution timed out after 30s")

    exec_service = TaskExecutionService(task_repository=task_repo, employee_service=emp_service)
    t = Task(
        id="t1",
        plan_id="p1",
        title="T1",
        description="D1",
        status=TaskStatus.READY,
        retry_count=0,
        max_retries=2,
    )

    result = await exec_service.execute_task(t, employee_id="emp-1", assignment_id="asgn-1")
    assert result.status == TaskStatus.FAILED
    assert result.retry_count == 1


# 7. Agent Runtime failure
@pytest.mark.asyncio
async def test_fm07_agent_runtime_failure() -> None:
    task_repo = MagicMock()
    emp_service = AsyncMock()
    emp_service.execute_work.side_effect = RuntimeError(
        "Agent runtime error: tool execution failed"
    )

    exec_service = TaskExecutionService(task_repository=task_repo, employee_service=emp_service)
    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)

    result = await exec_service.execute_task(t, employee_id="emp-1", assignment_id="asgn-1")
    assert result.status == TaskStatus.FAILED


# 8. Provider failure
@pytest.mark.asyncio
async def test_fm08_provider_failure() -> None:
    task_repo = MagicMock()
    emp_service = AsyncMock()
    emp_service.execute_work.side_effect = RuntimeError("Groq API provider unavailable 503")

    exec_service = TaskExecutionService(task_repository=task_repo, employee_service=emp_service)
    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)

    result = await exec_service.execute_task(t, employee_id="emp-1", assignment_id="asgn-1")
    assert result.status == TaskStatus.FAILED
    assert "Groq API provider unavailable" in result.metadata["last_execution_error"]


# 9. Retry exhaustion
@pytest.mark.asyncio
async def test_fm09_retry_exhaustion() -> None:
    task_repo = MagicMock()
    lifecycle = TaskLifecycleService(task_repository=task_repo)

    t = Task(
        id="t1",
        plan_id="p1",
        title="T1",
        description="D1",
        status=TaskStatus.FAILED,
        retry_count=3,
        max_retries=3,
    )
    task_repo.get_by_id.return_value = t

    with pytest.raises(TaskValidationError, match="exhausted max retries"):
        await lifecycle.retry_task("t1")


# 10. Duplicate scheduler invocation
@pytest.mark.asyncio
async def test_fm10_duplicate_scheduler_invocation() -> None:
    task_repo = MagicMock()
    claim_service = MagicMock()
    exec_service = AsyncMock()

    scheduler = TaskSchedulerService(task_repo, claim_service, exec_service)
    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)

    task_repo.get_by_status.return_value = [t]
    # First invocation succeeds
    claim_service.claim_task.side_effect = [t, TaskClaimError("Already claimed")]

    res1 = await scheduler.schedule_next_task(worker_id="worker-1")
    res2 = await scheduler.schedule_next_task(worker_id="worker-2")

    assert res1 is not None
    assert res2 is None


# 11. Concurrent task claim
def test_fm11_concurrent_task_claim() -> None:
    task_repo = MagicMock()
    service = TaskClaimService(task_repo)
    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)
    task_repo.get_by_id.return_value = t
    task_repo.save.side_effect = lambda x: x

    claimed1 = service.claim_task("t1", worker_id="w1")
    assert claimed1.status == TaskStatus.ASSIGNED

    # Concurrent attempt on ASSIGNED status fails
    with pytest.raises(TaskClaimError, match="cannot be claimed"):
        service.claim_task("t1", worker_id="w2")


# 12. Checkpoint/runtime interruption
@pytest.mark.asyncio
async def test_fm12_checkpoint_runtime_interruption() -> None:
    task_repo = MagicMock()
    emp_service = AsyncMock()
    emp_service.execute_work.side_effect = KeyboardInterrupt("SIGKILL during execution")

    exec_service = TaskExecutionService(task_repository=task_repo, employee_service=emp_service)
    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)

    with pytest.raises(KeyboardInterrupt):
        await exec_service.execute_task(t, employee_id="emp-1", assignment_id="asgn-1")


# 13. Invalid task transition
def test_fm13_invalid_task_transition() -> None:
    t = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.CREATED)
    with pytest.raises(InvalidStateTransitionError):
        t.transition_to(TaskStatus.COMPLETED)


# 14. Invalid dependency (self dependency)
def test_fm14_invalid_self_dependency() -> None:
    with pytest.raises(TaskDependencyError, match="cannot depend on itself"):
        TaskDependency(id="d1", predecessor_task_id="t1", successor_task_id="t1")


# 15. Dependent task blocked after predecessor failure
def test_fm15_dependent_task_blocked_after_predecessor_failure() -> None:
    evaluator = ReadinessEvaluator()
    graph = TaskGraph()

    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.FAILED)
    t2 = Task(id="t2", plan_id="p1", title="T2", description="D2", status=TaskStatus.PLANNED)
    graph.add_task(t1)
    graph.add_task(t2)
    graph.add_dependency(TaskDependency(id="d1", predecessor_task_id="t1", successor_task_id="t2"))

    is_ready, reasons = evaluator.evaluate_task(t2, graph)
    assert not is_ready
    assert BlockReason.DEPENDENCY_FAILED in reasons
