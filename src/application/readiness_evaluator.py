"""
Deterministic Readiness Evaluator Service for Task Engine.
"""

from src.domain.task import BlockReason, Task, TaskStatus
from src.domain.task_graph import TaskGraph


class ReadinessEvaluator:
    """
    Evaluates whether a Task is READY for execution based strictly on
    predecessor dependency statuses and parent task constraints.
    Does NOT invoke any LLM or external non-deterministic provider.
    """

    def evaluate_task(self, task: Task, graph: TaskGraph) -> tuple[bool, list[BlockReason]]:
        """
        Evaluate task readiness against the current dependency graph.
        Returns (is_ready, block_reasons).
        """
        # If task is already completed, approved, in progress, assigned, or cancelled,
        # it is not eligible for READY state evaluation.
        if task.status in {
            TaskStatus.COMPLETED,
            TaskStatus.APPROVED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.ASSIGNED,
            TaskStatus.REVIEW,
            TaskStatus.CANCELLED,
        }:
            return False, []

        is_ready, reasons = graph.evaluate_readiness(task.id)

        # Check parent task constraint if present
        if task.parent_task_id and task.parent_task_id in graph.tasks:
            parent = graph.tasks[task.parent_task_id]
            if parent.status in {TaskStatus.CANCELLED, TaskStatus.FAILED}:
                is_ready = False
                if BlockReason.POLICY_BLOCK not in reasons:
                    reasons.append(BlockReason.POLICY_BLOCK)

        return is_ready, reasons

    def update_task_readiness(self, task: Task, graph: TaskGraph) -> bool:
        """
        Evaluate and update the Task entity's status to READY or BLOCKED.
        Returns True if status changed.
        """
        if task.status not in {TaskStatus.PLANNED, TaskStatus.BLOCKED, TaskStatus.FAILED}:
            return False

        is_ready, reasons = self.evaluate_task(task, graph)

        if is_ready:
            if task.status != TaskStatus.READY:
                task.status = TaskStatus.READY
                task.block_reasons.clear()
                return True
        else:
            if task.status != TaskStatus.BLOCKED or task.block_reasons != reasons:
                task.status = TaskStatus.BLOCKED
                task.block_reasons = reasons
                return True

        return False
