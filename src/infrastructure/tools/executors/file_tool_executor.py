"""
File Tool Executor Adapter for Phase 8 Workspace File Operations.
Handles READ_FILE, WRITE_FILE, DELETE_FILE, and list_files within sandboxed workspace boundaries.
"""

import os
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
from src.infrastructure.tools.sandboxing import SandboxExecutionBoundary


class FileToolExecutor(ToolExecutorInterface):
    def __init__(self, sandbox: SandboxExecutionBoundary | None = None) -> None:
        self.sandbox = sandbox or SandboxExecutionBoundary()

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
            if cap == ToolCapability.READ_FILE:
                rel_path = args.get("path") or args.get("filename")
                if not rel_path:
                    raise ValueError("Argument 'path' is required for READ_FILE capability.")

                target_path = self.sandbox.sanitize_path(rel_path, workspace_id=request.workspace_id)
                if not target_path.exists():
                    raise FileNotFoundError(f"File '{rel_path}' not found in workspace '{request.workspace_id}'.")

                content = target_path.read_text(encoding="utf-8")
                truncated = self.sandbox.truncate_output(content)
                elapsed = (time.time() - start_time) * 1000

                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={"path": rel_path, "content": truncated, "size_bytes": len(content.encode("utf-8"))},
                    execution_time_ms=elapsed,
                )

            elif cap == ToolCapability.WRITE_FILE:
                rel_path = args.get("path") or args.get("filename")
                content = args.get("content", "")
                if not rel_path:
                    raise ValueError("Argument 'path' is required for WRITE_FILE capability.")

                target_path = self.sandbox.sanitize_path(rel_path, workspace_id=request.workspace_id)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(content, encoding="utf-8")
                elapsed = (time.time() - start_time) * 1000

                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={"path": rel_path, "written_bytes": len(content.encode("utf-8")), "success": True},
                    execution_time_ms=elapsed,
                )

            elif cap == ToolCapability.DELETE_FILE:
                rel_path = args.get("path") or args.get("filename")
                if not rel_path:
                    raise ValueError("Argument 'path' is required for DELETE_FILE capability.")

                target_path = self.sandbox.sanitize_path(rel_path, workspace_id=request.workspace_id)
                if target_path.exists():
                    target_path.unlink()

                elapsed = (time.time() - start_time) * 1000
                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={"path": rel_path, "deleted": True},
                    execution_time_ms=elapsed,
                )

            else:
                raise ValueError(f"FileToolExecutor does not support capability '{cap.value}'.")

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.FAILED,
                error_message=str(exc),
                execution_time_ms=elapsed,
            )
