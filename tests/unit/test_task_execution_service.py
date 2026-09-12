"""
Unit tests for TaskExecutionService execution, REVIEW boundary, and retry handling.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.task_execution_service import TaskExecutionService
from src.domain.task import Task, TaskStatus


@pytest.mark.asyncio
async def test_task_execution_success_transitions_to_review() -> None:
    task_repo = MagicMock()
    employee_service = AsyncMock()
    event_dispatcher = MagicMock()
    event_dispatcher.publish = AsyncMock()

    service = TaskExecutionService(
        task_repository=task_repo,
        employee_service=employee_service,
        event_dispatcher=event_dispatcher,
    )

    task = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)
    task_repo.save.side_effect = lambda t: t

    mock_run = MagicMock()
    mock_run.id = "run-100"
    mock_run.output = "Task executed successfully"
    mock_run.status = "SUCCESS"
    employee_service.execute_work.return_value = mock_run

    executed = await service.execute_task(
        task=task,
        employee_id="emp-1",
        assignment_id="asgn-1",
    )

    # False Completion Prevention Verification: Task goes to REVIEW, NOT COMPLETED directly!
    assert executed.status == TaskStatus.REVIEW
    assert executed.execution_run_id == "run-100"
    assert executed.assigned_employee_id == "emp-1"
    assert executed.assignment_id == "asgn-1"
    assert executed.result["output"] == "Task executed successfully"


@pytest.mark.asyncio
async def test_task_execution_failure_retry_policy() -> None:
    task_repo = MagicMock()
    employee_service = AsyncMock()
    event_dispatcher = MagicMock()
    event_dispatcher.publish = AsyncMock()

    service = TaskExecutionService(
        task_repository=task_repo,
        employee_service=employee_service,
        event_dispatcher=event_dispatcher,
    )

    task = Task(
        id="t1",
        plan_id="p1",
        title="T1",
        description="D1",
        status=TaskStatus.READY,
        retry_count=0,
        max_retries=2,
    )
    task_repo.save.side_effect = lambda t: t

    employee_service.execute_work.side_effect = Exception("Model provider timeout")

    executed = await service.execute_task(
        task=task,
        employee_id="emp-1",
        assignment_id="asgn-1",
    )

    assert executed.status == TaskStatus.FAILED
    assert executed.retry_count == 1
    assert executed.metadata["last_execution_error"] == "Model provider timeout"
