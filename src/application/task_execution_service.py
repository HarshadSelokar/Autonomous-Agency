"""
Task Execution Service integrating Phase 2 Employee Framework,
Assignment allocation, Agent Runtime execution, and REVIEW state boundary.
"""

import uuid
from typing import Any

from src.application.employee_service import EmployeeService
from src.application.event_dispatcher import EventDispatcher
from src.domain.events import (
    TaskExecutionFailedEvent,
    TaskExecutionStartedEvent,
    TaskRetryScheduledEvent,
    TaskReviewRequestedEvent,
)
from src.domain.task import Task, TaskStatus
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


class TaskExecutionService:
    """
    Task Execution Adapter delegating actual organizational work execution to Phase 2
    EmployeeService, linking AgentRun to Task, managing retries, and enforcing
    the REVIEW state boundary to prevent false auto-completion.
    """

    def __init__(
        self,
        task_repository: SQLAlchemyTaskRepository,
        employee_service: EmployeeService | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.task_repo = task_repository
        self.employee_service = employee_service
        self.event_dispatcher = event_dispatcher

    async def execute_task(
        self,
        task: Task,
        employee_id: str,
        assignment_id: str,
        execution_context: dict[str, Any] | None = None,
    ) -> Task:
        """
        Execute a Task assigned to employee_id.
        Transitions task: ASSIGNED -> IN_PROGRESS -> REVIEW (on success) or READY/FAILED.
        """
        task.assigned_employee_id = employee_id
        task.assignment_id = assignment_id

        if task.status == TaskStatus.READY:
            task.transition_to(TaskStatus.ASSIGNED)
            task.transition_to(TaskStatus.IN_PROGRESS)
        elif task.status in {TaskStatus.ASSIGNED, TaskStatus.REWORK}:
            task.transition_to(TaskStatus.IN_PROGRESS)

        self.task_repo.save(task)

        # 2. Invoke Employee execution if EmployeeService is provided
        if self.employee_service:
            try:
                run_result = await self.employee_service.execute_work(
                    employee_id=employee_id,
                    objective=f"{task.title}: {task.description}",
                    task_id=task.id,
                )
                run_id = getattr(run_result, "id", str(uuid.uuid4()))
                task.execution_run_id = run_id
                task.result = {
                    "output": getattr(run_result, "output", str(run_result)),
                    "status": getattr(run_result, "status", "SUCCESS"),
                }

                if self.event_dispatcher:
                    await self.event_dispatcher.publish(
                        TaskExecutionStartedEvent(
                            task_id=task.id,
                            employee_id=employee_id,
                            execution_run_id=run_id,
                        )
                    )

                # Transition to REVIEW (False Completion Prevention: Agent "Done" != Task COMPLETED)
                task.transition_to(TaskStatus.REVIEW)
                self.task_repo.save(task)

                if self.event_dispatcher:
                    await self.event_dispatcher.publish(
                        TaskReviewRequestedEvent(
                            task_id=task.id,
                            execution_run_id=run_id,
                        )
                    )

                return task

            except Exception as exc:
                error_msg = str(exc)
                task.metadata["last_execution_error"] = error_msg

                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    # Return task to FAILED or READY state for bounded retry
                    task.transition_to(TaskStatus.FAILED)
                    self.task_repo.save(task)

                    if self.event_dispatcher:
                        await self.event_dispatcher.publish(
                            TaskRetryScheduledEvent(
                                task_id=task.id,
                                retry_count=task.retry_count,
                                max_retries=task.max_retries,
                            )
                        )
                else:
                    task.transition_to(TaskStatus.FAILED)
                    self.task_repo.save(task)

                    if self.event_dispatcher:
                        await self.event_dispatcher.publish(
                            TaskExecutionFailedEvent(
                                task_id=task.id,
                                execution_run_id=task.execution_run_id or "",
                                error=error_msg,
                            )
                        )
                return task
        else:
            # Simulated execution mode for testing/standalone scheduler
            mock_run_id = f"run-{uuid.uuid4().hex[:8]}"
            task.execution_run_id = mock_run_id
            task.result = {"output": f"Simulated output for task {task.title}"}
            task.transition_to(TaskStatus.REVIEW)
            self.task_repo.save(task)
            return task
