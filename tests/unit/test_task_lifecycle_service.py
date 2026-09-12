"""
Unit tests for TaskLifecycleService review, rework, approval, and retry operations.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.task_lifecycle_service import TaskLifecycleService
from src.domain.exceptions import TaskValidationError
from src.domain.task import Task, TaskStatus


@pytest.mark.asyncio
async def test_review_task_approved_completes_task() -> None:
    task_repo = MagicMock()
    graph_service = MagicMock()
    event_dispatcher = MagicMock()
    event_dispatcher.publish = AsyncMock()

    service = TaskLifecycleService(
        task_repository=task_repo,
        dependency_graph_service=graph_service,
        event_dispatcher=event_dispatcher,
    )

    task = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.REVIEW)
    task_repo.get_by_id.return_value = task
    task_repo.save.side_effect = lambda t: t

    reviewed = await service.review_task("t1", approved=True, reviewer_id="mgr-1")

    assert reviewed.status == TaskStatus.COMPLETED
    graph_service.propagate_task_state_change.assert_called_once_with("t1")


@pytest.mark.asyncio
async def test_review_task_rejected_transitions_to_rework() -> None:
    task_repo = MagicMock()
    service = TaskLifecycleService(task_repository=task_repo)

    task = Task(
        id="t1",
        plan_id="p1",
        title="T1",
        description="D1",
        status=TaskStatus.REVIEW,
        execution_run_id="run-1",
    )
    task_repo.get_by_id.return_value = task
    task_repo.save.side_effect = lambda t: t

    reviewed = await service.review_task(
        "t1", approved=False, reviewer_id="mgr-1", feedback="Fix data format"
    )

    assert reviewed.status == TaskStatus.REWORK
    assert len(reviewed.metadata["rework_history"]) == 1
    assert reviewed.metadata["rework_history"][0]["feedback"] == "Fix data format"


@pytest.mark.asyncio
async def test_retry_failed_task_success() -> None:
    task_repo = MagicMock()
    service = TaskLifecycleService(task_repository=task_repo)

    task = Task(
        id="t1",
        plan_id="p1",
        title="T1",
        description="D1",
        status=TaskStatus.FAILED,
        retry_count=1,
        max_retries=3,
    )
    task_repo.get_by_id.return_value = task
    task_repo.save.side_effect = lambda t: t

    retried = await service.retry_task("t1")

    assert retried.status == TaskStatus.READY
    assert retried.retry_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_retries_rejected() -> None:
    task_repo = MagicMock()
    service = TaskLifecycleService(task_repository=task_repo)

    task = Task(
        id="t1",
        plan_id="p1",
        title="T1",
        description="D1",
        status=TaskStatus.FAILED,
        retry_count=3,
        max_retries=3,
    )
    task_repo.get_by_id.return_value = task

    with pytest.raises(TaskValidationError, match="exhausted max retries"):
        await service.retry_task("t1")
