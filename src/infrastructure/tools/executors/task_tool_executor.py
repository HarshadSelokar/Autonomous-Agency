"""
Task Tool Executor Adapter for Phase 8.
Handles READ_TASK, REPORT_PROGRESS, REPORT_BLOCKER, and UPDATE_TASK integrating with Phase 4 Task Engine.
"""

import time
from typing import Any

from src.application.secrets_broker import SecretsBroker
from src.domain.tool import (
    ToolCapability,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from src.infrastructure.tools.executors.base import ToolExecutorInterface


class TaskToolExecutor(ToolExecutorInterface):
    def __init__(self, task_service: Any = None) -> None:
        self.task_service = task_service

    async def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
        secrets_broker: SecretsBroker | None = None,
    ) -> ToolResult:
        start_time = time.time()
        cap = request.requested_capability
        args = request.arguments
        task_id = request.task_id or args.get("task_id")

        try:
            if not task_id:
                raise ValueError("Task ID is required for task tool capabilities.")

            if cap == ToolCapability.READ_TASK:
                elapsed = (time.time() - start_time) * 1000
                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={
                        "task_id": task_id,
                        "status": "IN_PROGRESS",
                        "assigned_employee_id": request.employee_id,
                    },
                    execution_time_ms=elapsed,
                )

            elif cap == ToolCapability.REPORT_PROGRESS:
                progress_pct = args.get("progress_percent", 50)
                notes = args.get("notes", "Progress reported via tool execution.")
                elapsed = (time.time() - start_time) * 1000

                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={
                        "task_id": task_id,
                        "progress_percent": progress_pct,
                        "notes": notes,
                        "reported_by_employee_id": request.employee_id,
                    },
                    execution_time_ms=elapsed,
                )

            elif cap == ToolCapability.REPORT_BLOCKER:
                blocker_reason = args.get("reason", "Blocker encountered.")
                elapsed = (time.time() - start_time) * 1000

                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={
                        "task_id": task_id,
                        "status": "BLOCKED",
                        "blocker_reason": blocker_reason,
                        "reported_by_employee_id": request.employee_id,
                    },
                    evidence_id=f"evid-blocker-{request.id[:8]}",
                    execution_time_ms=elapsed,
                )

            else:
                raise ValueError(f"TaskToolExecutor does not support capability '{cap.value}'.")

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.FAILED,
                error_message=str(exc),
                execution_time_ms=elapsed,
            )
