import inspect
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


async def _maybe_await(res: Any) -> Any:
    if inspect.isawaitable(res):
        return await res
    return res


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
        task = await _maybe_await(self.task_repo.get_by_id(task_id))

        if task.status != TaskStatus.REVIEW:
            raise TaskValidationError(
                f"Task '{task_id}' cannot be reviewed: current status is "
                f"'{task.status.value}', expected 'REVIEW'."
            )

        if approved:
            task.transition_to(TaskStatus.APPROVED)
            if self.event_dispatcher:
                await _maybe_await(
                    self.event_dispatcher.publish(
                        TaskApprovedEvent(task_id=task.id, approved_by=reviewer_id)
                    )
                )

            task.transition_to(TaskStatus.COMPLETED)
            await _maybe_await(self.task_repo.save(task))

            if self.event_dispatcher:
                await _maybe_await(
                    self.event_dispatcher.publish(TaskCompletedEvent(task_id=task.id))
                )

            # Propagate readiness state change to downstream successors
            if self.graph_service:
                await _maybe_await(self.graph_service.propagate_task_state_change(task.id))

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
            await _maybe_await(self.task_repo.save(task))

            if self.event_dispatcher:
                await _maybe_await(
                    self.event_dispatcher.publish(
                        TaskReworkRequestedEvent(
                            task_id=task.id, reason=feedback or "Work rejected"
                        )
                    )
                )

        return task

    async def retry_task(self, task_id: str, force: bool = False) -> Task:
        """
        Retry a task currently in FAILED status if retry limits permit or if force=True.
        """
        task = await _maybe_await(self.task_repo.get_by_id(task_id))

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
        await _maybe_await(self.task_repo.save(task))

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(
                    TaskRetryScheduledEvent(
                        task_id=task.id,
                        retry_count=task.retry_count,
                        max_retries=task.max_retries,
                    )
                )
            )

        return task

    async def cancel_task(self, task_id: str, reason: str = "") -> Task:
        """
        Cancel a task, preserving audit history and updating downstream graph state.
        """
        task = await _maybe_await(self.task_repo.get_by_id(task_id))
        task.transition_to(TaskStatus.CANCELLED)
        task.metadata["cancellation_reason"] = reason
        await _maybe_await(self.task_repo.save(task))

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(TaskCancelledEvent(task_id=task.id, reason=reason))
            )

        if self.graph_service:
            await _maybe_await(self.graph_service.propagate_task_state_change(task.id))

        return task

    async def request_rework(self, task_id: str, reason: str = "") -> Task:
        """
        Transition task back to REWORK / IN_PROGRESS status for employee fix.
        """
        task = await _maybe_await(self.task_repo.get_by_id(task_id))
        task.transition_to(TaskStatus.REWORK)
        if "rework_history" not in task.metadata:
            task.metadata["rework_history"] = []
        task.metadata["rework_history"].append({"reason": reason, "timestamp": str(datetime.now(UTC)) if hasattr(datetime, "now") else ""})
        await _maybe_await(self.task_repo.save(task))
        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(TaskReworkRequestedEvent(task_id=task.id, reason=reason))
            )
        return task

    async def complete_task_with_verification(
        self,
        task_id: str,
        verification_engine: Any,
        recovery_engine: Any | None = None,
    ) -> tuple[Task, Any]:
        """
        Executes Phase 10 verification flow:
        Agent claim -> Verification Engine -> Result.
        If verified: COMPLETED.
        If failed: Recovery Engine triggered.
        """
        task = await _maybe_await(self.task_repo.get_by_id(task_id))
        result = verification_engine.verify_task(task_id)

        if result.is_verified:
            task.transition_to(TaskStatus.APPROVED)
            task.transition_to(TaskStatus.COMPLETED)
            await _maybe_await(self.task_repo.save(task))
            if self.event_dispatcher:
                await _maybe_await(self.event_dispatcher.publish(TaskCompletedEvent(task_id=task.id)))
            if self.graph_service:
                await _maybe_await(self.graph_service.propagate_task_state_change(task.id))
        else:
            if recovery_engine:
                recovery_engine.process_verification_failure(result)

        return task, result
