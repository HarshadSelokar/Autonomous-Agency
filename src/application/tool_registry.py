"""
ToolRegistry Application Layer for Phase 8.
Centralized, provider-neutral catalog for registering, discovering, and resolving tool definitions.
Guarantees that tool discovery never exposes secrets or bypasses backend authorization.
"""

from typing import Any

from src.domain.tool import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolStatus,
)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict[str, ToolDefinition]] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register or update a ToolDefinition in the registry."""
        tool.validate()
        if tool.id not in self._tools:
            self._tools[tool.id] = {}
        self._tools[tool.id][tool.version] = tool

    def unregister(self, tool_id: str, version: str | None = None) -> bool:
        """Deactivate or remove a tool from the registry."""
        if tool_id not in self._tools:
            return False
        if version:
            if version in self._tools[tool_id]:
                del self._tools[tool_id][version]
                if not self._tools[tool_id]:
                    del self._tools[tool_id]
                return True
            return False
        else:
            del self._tools[tool_id]
            return True

    def get_tool(self, tool_id: str, version: str | None = None) -> ToolDefinition | None:
        """Retrieve active ToolDefinition by tool_id and optional version."""
        if tool_id not in self._tools:
            return None
        versions = self._tools[tool_id]
        if not versions:
            return None

        if version:
            tool = versions.get(version)
        else:
            # Resolve highest / latest version
            latest_version = sorted(versions.keys())[-1]
            tool = versions.get(latest_version)

        if tool and tool.status == ToolStatus.ACTIVE:
            return tool
        return None

    def list_tools(
        self,
        category: ToolCategory | None = None,
        capability: ToolCapability | None = None,
    ) -> list[ToolDefinition]:
        """List active tools matching category and capability filters."""
        result: list[ToolDefinition] = []
        for versions in self._tools.values():
            for tool in versions.values():
                if tool.status != ToolStatus.ACTIVE:
                    continue
                if category and tool.category != category:
                    continue
                if capability and not tool.supports_capability(capability):
                    continue
                result.append(tool)
        return result

    def get_safe_metadata_for_agent(self) -> list[dict[str, Any]]:
        """
        Expose sanitized tool metadata for Agent LLM prompt context injection.
        Guarantees raw secrets, credentials, and internal endpoints are NEVER included.
        """
        metadata_list: list[dict[str, Any]] = []
        for versions in self._tools.values():
            for tool in versions.values():
                if tool.status != ToolStatus.ACTIVE:
                    continue
                metadata_list.append(
                    {
                        "tool_id": tool.id,
                        "name": tool.name,
                        "description": tool.description,
                        "version": tool.version,
                        "capabilities": [c.value for c in tool.capabilities],
                        "input_schema": tool.input_schema,
                        "permission_mode": tool.permission_mode.value,
                        "risk_level": tool.risk_level.value,
                    }
                )
        return metadata_list
