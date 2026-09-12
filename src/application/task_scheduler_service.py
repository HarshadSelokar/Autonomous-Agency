"""
Task Scheduler Service for Ready Task discovery, priority ordering,
atomic claiming, employee selection, and execution coordination.
"""

import inspect
import uuid
from typing import Any

from src.application.employee_selector import EmployeeSelector
from src.application.task_claim_service import TaskClaimService
from src.application.task_execution_service import TaskExecutionService
from src.domain.assignment import Assignment, AssignmentStatus
from src.domain.exceptions import TaskClaimError
from src.domain.task import Task, TaskStatus
from src.infrastructure.repositories.assignment_repository import (
    SQLAlchemyAssignmentRepository,
)
from src.infrastructure.repositories.employee_repository import (
    SQLAlchemyEmployeeRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


async def _maybe_await(res: Any) -> Any:
    if inspect.isawaitable(res):
        return await res
    return res


class TaskSchedulerService:
    """
    Deterministic Task Scheduler Service that discovers executable READY tasks,
    claims them atomically, matches eligible employees via EmployeeSelector,
    allocates assignments, and coordinates execution.
    """

    def __init__(
        self,
        task_repository: SQLAlchemyTaskRepository,
        claim_service: TaskClaimService,
        execution_service: TaskExecutionService,
        employee_selector: EmployeeSelector | None = None,
        employee_repository: SQLAlchemyEmployeeRepository | None = None,
        assignment_repository: SQLAlchemyAssignmentRepository | None = None,
    ) -> None:
        self.task_repo = task_repository
        self.claim_service = claim_service
        self.execution_service = execution_service
        self.employee_selector = employee_selector or EmployeeSelector()
        self.employee_repo = employee_repository
        self.assignment_repo = assignment_repository

    async def get_ready_tasks(self, plan_id: str | None = None) -> list[Task]:
        """
        Discover executable tasks in READY status, ordered by priority and creation time.
        """
        if plan_id:
            tasks = await _maybe_await(self.task_repo.get_by_plan_id(plan_id))
            ready = [t for t in tasks if t.status == TaskStatus.READY]
        else:
            ready = await _maybe_await(self.task_repo.get_by_status(TaskStatus.READY))

        # Sort deterministically: priority ascending (critical first), then created_at
        ready.sort(key=lambda t: (PRIORITY_ORDER.get(t.priority, 2), t.created_at))
        return ready

    async def schedule_next_task(
        self, worker_id: str = "scheduler-1", plan_id: str | None = None
    ) -> Task | None:
        """
        Find the highest-priority READY task, claim it atomically, match an employee,
        and trigger execution.
        """
        ready_tasks = await self.get_ready_tasks(plan_id)
        if not ready_tasks:
            return None

        for candidate in ready_tasks:
            try:
                # 1. Atomic claim
                claimed_task = await _maybe_await(
                    self.claim_service.claim_task(candidate.id, worker_id)
                )

                # 2. Employee Selection
                selected_emp_id = claimed_task.assigned_employee_id
                if not selected_emp_id and self.employee_repo:
                    all_employees = await _maybe_await(self.employee_repo.list_all())
                    eligible = self.employee_selector.find_eligible_employees(
                        employees=list(all_employees),
                        required_capabilities=claimed_task.required_capabilities,
                    )
                    if eligible:
                        selected_emp_id = eligible[0].id

                selected_emp_id = selected_emp_id or "unassigned-emp"

                # 3. Create Assignment record
                assignment_id = claimed_task.assignment_id or f"asgn-{uuid.uuid4().hex[:8]}"
                if self.assignment_repo and not claimed_task.assignment_id:
                    asgn = Assignment(
                        id=assignment_id,
                        work_item_id=claimed_task.work_item_id or claimed_task.id,
                        employee_id=selected_emp_id,
                        assigned_by=worker_id,
                        reason="TaskScheduler automated allocation",
                        status=AssignmentStatus.ACTIVE,
                    )
                    await _maybe_await(self.assignment_repo.save(asgn))

                # 4. Trigger Execution
                executed_task = await _maybe_await(
                    self.execution_service.execute_task(
                        task=claimed_task,
                        employee_id=selected_emp_id,
                        assignment_id=assignment_id,
                    )
                )
                return executed_task

            except TaskClaimError:
                # Concurrent worker claimed this task first, try next candidate
                continue

        return None

    async def run_scheduler_cycle(
        self, worker_id: str = "scheduler-1", max_tasks: int = 10
    ) -> list[Task]:
        """Run continuous scheduling pass up to max_tasks."""
        processed: list[Task] = []
        for _ in range(max_tasks):
            task = await self.schedule_next_task(worker_id=worker_id)
            if task is None:
                break
            processed.append(task)
        return processed
