"""
Unit tests for TaskClaimService and race condition prevention.
"""

from unittest.mock import MagicMock

import pytest

from src.application.task_claim_service import TaskClaimService
from src.domain.exceptions import TaskClaimError
from src.domain.task import Task, TaskStatus


@pytest.mark.asyncio
async def test_claim_ready_task_success() -> None:
    task_repo = MagicMock()
    service = TaskClaimService(task_repo)

    task = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)
    task_repo.get_by_id.return_value = task
    task_repo.save.side_effect = lambda t: t

    claimed = await service.claim_task("t1", worker_id="worker-1")

    assert claimed.status == TaskStatus.ASSIGNED
    assert claimed.metadata["claimed_by"] == "worker-1"
    task_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_claim_non_ready_task_fails() -> None:
    task_repo = MagicMock()
    service = TaskClaimService(task_repo)

    task = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.IN_PROGRESS)
    task_repo.get_by_id.return_value = task

    with pytest.raises(TaskClaimError, match="cannot be claimed"):
        await service.claim_task("t1", worker_id="worker-1")


@pytest.mark.asyncio
async def test_concurrent_claim_race_condition_protection() -> None:
    task_repo = MagicMock()
    service = TaskClaimService(task_repo)

    task = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.READY)

    # Worker 1 gets task in READY status and mutates it to ASSIGNED
    task_repo.get_by_id.return_value = task

    def mock_save(t: Task) -> Task:
        # Save updates the status
        t.status = TaskStatus.ASSIGNED
        return t

    task_repo.save.side_effect = mock_save

    worker1_claimed = await service.claim_task("t1", worker_id="worker-1")
    assert worker1_claimed.status == TaskStatus.ASSIGNED

    # Worker 2 tries to claim the same task object now in ASSIGNED status
    with pytest.raises(TaskClaimError, match="cannot be claimed"):
        await service.claim_task("t1", worker_id="worker-2")
