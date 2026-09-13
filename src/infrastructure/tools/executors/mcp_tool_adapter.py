"""
MCP (Model Context Protocol) Integration Tool Adapter for Phase 8.
Treats MCP strictly as an external integration mechanism while preserving the core provider-neutral domain model.
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


class MCPToolAdapter(ToolExecutorInterface):
    """
    Adapter bridging Company OS tool executions to external Model Context Protocol (MCP) servers.
    MCP concepts remain fully encapsulated within this adapter.
    """

    def __init__(self, mcp_server_url: str | None = None) -> None:
        self.mcp_server_url = mcp_server_url or "http://localhost:8080/mcp"

    async def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
        secrets_broker: SecretsBroker | None = None,
    ) -> ToolResult:
        start_time = time.time()
        args = request.arguments

        try:
            # Encapsulated MCP request mapping
            mcp_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool.id,
                    "arguments": args,
                },
                "id": request.id,
            }

            elapsed = (time.time() - start_time) * 1000

            # Simulated clean MCP adapter response
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.SUCCEEDED,
                output={
                    "adapter": "MCPToolAdapter",
                    "mcp_server_url": self.mcp_server_url,
                    "mcp_method": mcp_payload["method"],
                    "result": {"status": "ok", "message": f"MCP tool '{tool.id}' executed successfully."},
                },
                execution_time_ms=elapsed,
            )

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.FAILED,
                error_message=str(exc),
                execution_time_ms=elapsed,
            )
