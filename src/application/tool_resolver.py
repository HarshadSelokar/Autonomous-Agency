"""
ToolResolver Application Layer for Phase 8.
Deterministically resolves requested tools, validates capability containment,
checks permission modes, and prevents permission escalation by LLM models.
"""

from dataclasses import dataclass
from typing import Any

from src.application.tool_registry import ToolRegistry
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolDefinition,
    ToolRequest,
    ToolStatus,
    ToolValidationError,
)


@dataclass
class ToolResolutionResult:
    tool: ToolDefinition | None
    permission_mode: PermissionMode
    is_allowed: bool
    requires_approval: bool
    rejection_reason: str | None = None


class ToolResolver:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def resolve(self, request: ToolRequest, requesting_employee: Any | None = None) -> ToolResolutionResult:
        """
        Deterministically resolve requested tool, validate capability containment,
        and evaluate permission requirements.
        """
        # 1. Resolve Tool Definition
        tool = self.registry.get_tool(request.tool_id, request.tool_version)
        if not tool:
            return ToolResolutionResult(
                tool=None,
                permission_mode=PermissionMode.BLOCKED,
                is_allowed=False,
                requires_approval=False,
                rejection_reason=f"Tool '{request.tool_id}' (version: '{request.tool_version}') is unknown or inactive.",
            )

        # 2. Validate Capability Inclusion (requested_capability ∈ tool.capabilities)
        if not tool.supports_capability(request.requested_capability):
            return ToolResolutionResult(
                tool=tool,
                permission_mode=PermissionMode.BLOCKED,
                is_allowed=False,
                requires_approval=False,
                rejection_reason=(
                    f"Tool '{tool.id}' does NOT support requested capability '{request.requested_capability.value}'."
                ),
            )

        # 3. Determine Permission Mode Boundaries
        mode = tool.permission_mode

        if mode == PermissionMode.BLOCKED:
            return ToolResolutionResult(
                tool=tool,
                permission_mode=PermissionMode.BLOCKED,
                is_allowed=False,
                requires_approval=False,
                rejection_reason=f"Tool '{tool.id}' capability '{request.requested_capability.value}' is BLOCKED by organizational policy.",
            )

        if mode == PermissionMode.APPROVAL:
            return ToolResolutionResult(
                tool=tool,
                permission_mode=PermissionMode.APPROVAL,
                is_allowed=False,
                requires_approval=True,
                rejection_reason=f"Tool '{tool.id}' capability '{request.requested_capability.value}' requires explicit managerial approval.",
            )

        # AUTO Mode
        return ToolResolutionResult(
            tool=tool,
            permission_mode=PermissionMode.AUTO,
            is_allowed=True,
            requires_approval=False,
            rejection_reason=None,
        )
