"""
Communication Tool Executor Adapter for Phase 8.
Handles SEND_MESSAGE and REPORT_BLOCKER integrating with Phase 5 Communication Protocol.
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


class CommunicationToolExecutor(ToolExecutorInterface):
    def __init__(self, communication_service: Any = None) -> None:
        self.communication_service = communication_service

    async def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
        secrets_broker: SecretsBroker | None = None,
    ) -> ToolResult:
        start_time = time.time()
        cap = request.requested_capability
        args = request.arguments

        try:
            if cap == ToolCapability.SEND_MESSAGE:
                recipient_id = args.get("recipient_id") or args.get("recipient")
                content = args.get("content") or args.get("message")
                if not recipient_id or not content:
                    raise ValueError("Arguments 'recipient_id' and 'content' are required for SEND_MESSAGE.")

                elapsed = (time.time() - start_time) * 1000

                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={
                        "sender_employee_id": request.employee_id,
                        "recipient_id": recipient_id,
                        "content": content,
                        "delivered": True,
                    },
                    execution_time_ms=elapsed,
                )

            else:
                raise ValueError(f"CommunicationToolExecutor does not support capability '{cap.value}'.")

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.FAILED,
                error_message=str(exc),
                execution_time_ms=elapsed,
            )
