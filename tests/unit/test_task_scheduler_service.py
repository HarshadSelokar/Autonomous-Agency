"""
Unit tests for TaskSchedulerService discovery, priority ordering, and cycle execution.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.task_scheduler_service import TaskSchedulerService
from src.domain.task import Task, TaskStatus


@pytest.mark.asyncio
async def test_scheduler_get_ready_tasks_priority_ordering() -> None:
    task_repo = MagicMock()
    claim_service = MagicMock()
    execution_service = AsyncMock()

    scheduler = TaskSchedulerService(
        task_repository=task_repo,
        claim_service=claim_service,
        execution_service=execution_service,
    )

    t_low = Task(
        id="t1", plan_id="p1", title="T1", description="D1", priority="low", status=TaskStatus.READY
    )
    t_critical = Task(
        id="t2",
        plan_id="p1",
        title="T2",
        description="D2",
        priority="critical",
        status=TaskStatus.READY,
    )
    t_high = Task(
        id="t3",
        plan_id="p1",
        title="T3",
        description="D3",
        priority="high",
        status=TaskStatus.READY,
    )

    task_repo.get_by_status.return_value = [t_low, t_critical, t_high]

    ready = await scheduler.get_ready_tasks()
    assert [t.id for t in ready] == ["t2", "t3", "t1"]


@pytest.mark.asyncio
async def test_schedule_next_task_execution() -> None:
    task_repo = MagicMock()
    claim_service = MagicMock()
    execution_service = AsyncMock()

    scheduler = TaskSchedulerService(
        task_repository=task_repo,
        claim_service=claim_service,
        execution_service=execution_service,
    )

    t_ready = Task(
        id="t1",
        plan_id="p1",
        title="T1",
        description="D1",
        priority="high",
        status=TaskStatus.READY,
    )
    task_repo.get_by_status.return_value = [t_ready]
    claim_service.claim_task.return_value = t_ready

    mock_executed = Task(
        id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.REVIEW
    )
    execution_service.execute_task.return_value = mock_executed

    result = await scheduler.schedule_next_task(worker_id="w1")

    assert result is not None
    assert result.status == TaskStatus.REVIEW
    claim_service.claim_task.assert_called_once_with("t1", "w1")
    execution_service.execute_task.assert_awaited_once()
