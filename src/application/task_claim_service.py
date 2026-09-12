"""
Atomic Task Claiming Service to prevent race conditions and duplicate execution.
"""

from typing import Any

from src.domain.exceptions import TaskClaimError
from src.domain.task import Task, TaskStatus
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


class TaskClaimService:
    """
    Atomic task claim coordinator preventing multi-worker duplicate execution.
    Only one worker can successfully claim a READY task.
    """

    def __init__(self, task_repository: SQLAlchemyTaskRepository) -> None:
        self.task_repo = task_repository

    def claim_task(
        self, task_id: str, worker_id: str, metadata: dict[str, Any] | None = None
    ) -> Task:
        """
        Atomically claim a task in READY status for worker_id.
        Raises TaskClaimError if task is not in READY status or already claimed.
        """
        task = self.task_repo.get_by_id(task_id)

        if task.status != TaskStatus.READY:
            raise TaskClaimError(
                f"Task '{task_id}' cannot be claimed by worker '{worker_id}': "
                f"current status is '{task.status.value}', expected '{TaskStatus.READY.value}'."
            )

        task.transition_to(TaskStatus.ASSIGNED)
        task.metadata["claimed_by"] = worker_id
        if metadata:
            task.metadata.update(metadata)

        saved_task = self.task_repo.save(task)
        return saved_task
