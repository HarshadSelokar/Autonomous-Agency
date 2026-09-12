"""
Task Lifecycle Service managing REVIEW, REWORK, APPROVAL, RETRY, and CANCELLATION operations.
"""

from typing import Any

from src.application.dependency_graph_service import DependencyGraphService
from src.application.event_dispatcher import EventDispatcher
from src.domain.events import (
    TaskApprovedEvent,
    TaskCancelledEvent,
    TaskCompletedEvent,
    TaskRetryScheduledEvent,
    TaskReworkRequestedEvent,
)
from src.domain.exceptions import TaskValidationError
from src.domain.task import Task, TaskStatus
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


class TaskLifecycleService:
    """
    Service governing task review, rework feedback, approval, completion,
    cancellation, and bounded retry operations.
    """

    def __init__(
        self,
        task_repository: SQLAlchemyTaskRepository,
        dependency_graph_service: DependencyGraphService | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.task_repo = task_repository
        self.graph_service = dependency_graph_service
        self.event_dispatcher = event_dispatcher

    async def review_task(
        self,
        task_id: str,
        approved: bool,
        reviewer_id: str,
        feedback: str | None = None,
    ) -> Task:
        """
        Review a task currently in REVIEW status.
        If approved: transitions REVIEW -> APPROVED -> COMPLETED and propagates readiness.
        If rejected: transitions REVIEW -> REWORK and preserves execution history.
        """
        task = self.task_repo.get_by_id(task_id)

        if task.status != TaskStatus.REVIEW:
            raise TaskValidationError(
                f"Task '{task_id}' cannot be reviewed: current status is "
                f"'{task.status.value}', expected 'REVIEW'."
            )

        if approved:
            task.transition_to(TaskStatus.APPROVED)
            if self.event_dispatcher:
                await self.event_dispatcher.publish(
                    TaskApprovedEvent(task_id=task.id, approved_by=reviewer_id)
                )

            task.transition_to(TaskStatus.COMPLETED)
            self.task_repo.save(task)

            if self.event_dispatcher:
                await self.event_dispatcher.publish(TaskCompletedEvent(task_id=task.id))

            # Propagate readiness state change to downstream successors
            if self.graph_service:
                self.graph_service.propagate_task_state_change(task.id)

        else:
            task.transition_to(TaskStatus.REWORK)
            if "rework_history" not in task.metadata:
                task.metadata["rework_history"] = []

            rework_entry: dict[str, Any] = {
                "reviewer_id": reviewer_id,
                "feedback": feedback or "Work rejected during review.",
                "previous_execution_run_id": task.execution_run_id,
            }
            task.metadata["rework_history"].append(rework_entry)
            self.task_repo.save(task)

            if self.event_dispatcher:
                await self.event_dispatcher.publish(
                    TaskReworkRequestedEvent(task_id=task.id, reason=feedback or "Work rejected")
                )

        return task

    async def retry_task(self, task_id: str, force: bool = False) -> Task:
        """
        Retry a task currently in FAILED status if retry limits permit or if force=True.
        """
        task = self.task_repo.get_by_id(task_id)

        if task.status != TaskStatus.FAILED:
            raise TaskValidationError(
                f"Task '{task_id}' cannot be retried: current status is "
                f"'{task.status.value}', expected 'FAILED'."
            )

        if not force and task.retry_count >= task.max_retries:
            raise TaskValidationError(
                f"Task '{task_id}' has exhausted max retries "
                f"({task.retry_count}/{task.max_retries})."
            )

        task.retry_count += 1
        task.transition_to(TaskStatus.READY)
        self.task_repo.save(task)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                TaskRetryScheduledEvent(
                    task_id=task.id,
                    retry_count=task.retry_count,
                    max_retries=task.max_retries,
                )
            )

        return task

    async def cancel_task(self, task_id: str, reason: str = "") -> Task:
        """
        Cancel a task, preserving audit history and updating downstream graph state.
        """
        task = self.task_repo.get_by_id(task_id)
        task.transition_to(TaskStatus.CANCELLED)
        task.metadata["cancellation_reason"] = reason
        self.task_repo.save(task)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(TaskCancelledEvent(task_id=task.id, reason=reason))

        if self.graph_service:
            self.graph_service.propagate_task_state_change(task.id)

        return task
