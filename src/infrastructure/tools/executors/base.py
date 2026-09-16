"""
Base ToolExecutorInterface for Phase 8.
Provider-neutral abstraction for executing tools across workspace, artifact, task, communication, HTTP, and browser adapters.
"""

from abc import ABC, abstractmethod

from src.application.secrets_broker import SecretsBroker
from src.domain.tool import ToolDefinition, ToolRequest, ToolResult


class ToolExecutorInterface(ABC):
    """Abstract interface for all tool execution adapters."""

    @abstractmethod
    async def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
        secrets_broker: SecretsBroker | None = None,
    ) -> ToolResult:
        """Execute the tool request and return a structured ToolResult."""
        pass
