"""
Unit tests for TaskLifecycleService + Verification integration (Phase 10).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.task_lifecycle_service import TaskLifecycleService
from src.domain.task import Task, TaskStatus
from src.domain.verification import VerificationResult, VerificationStatus


@pytest.mark.asyncio
async def test_complete_task_with_verification_success():
    task_repo = AsyncMock()
    task = Task(id="t1", plan_id="p1", title="Test Task", description="Desc", status=TaskStatus.REVIEW)
    task_repo.get_by_id.return_value = task
    task_repo.save.return_value = task

    verif_engine = MagicMock()
    verif_engine.verify_task.return_value = VerificationResult(
        verification_id="v1",
        task_id="t1",
        outcome_id="o1",
        status=VerificationStatus.VERIFIED,
    )

    service = TaskLifecycleService(task_repository=task_repo)
    res_task, res_verif = await service.complete_task_with_verification(
        task_id="t1",
        verification_engine=verif_engine,
    )

    assert res_task.status == TaskStatus.COMPLETED
    assert res_verif.is_verified


@pytest.mark.asyncio
async def test_complete_task_with_verification_failure_triggers_recovery():
    task_repo = AsyncMock()
    task = Task(id="t2", plan_id="p1", title="Failed Task", description="Desc", status=TaskStatus.REVIEW)
    task_repo.get_by_id.return_value = task

    verif_engine = MagicMock()
    failed_result = VerificationResult(
        verification_id="v2",
        task_id="t2",
        outcome_id="o1",
        status=VerificationStatus.FAILED,
    )
    verif_engine.verify_task.return_value = failed_result

    recovery_engine = MagicMock()

    service = TaskLifecycleService(task_repository=task_repo)
    res_task, res_verif = await service.complete_task_with_verification(
        task_id="t2",
        verification_engine=verif_engine,
        recovery_engine=recovery_engine,
    )

    assert res_task.status == TaskStatus.REVIEW  # Task not completed
    assert not res_verif.is_verified
    recovery_engine.process_verification_failure.assert_called_once_with(failed_result)
