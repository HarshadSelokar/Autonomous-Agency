"""
Durable Workflow Engine 2.0 Domain Entities and State Machines (Phase 37).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowNodeType(str, Enum):
    TASK = "TASK"
    AGENT = "AGENT"
    TOOL = "TOOL"
    APPROVAL = "APPROVAL"
    CONDITIONAL = "CONDITIONAL"


@dataclass(frozen=True)
class WorkflowNode:
    id: str
    name: str
    node_type: WorkflowNodeType = WorkflowNodeType.TASK
    action_target: str = ""
    dependencies: list[str] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    id: str
    tenant_id: str
    name: str
    version: int = 1
    nodes: list[WorkflowNode] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowInstance:
    id: str
    tenant_id: str
    definition_id: str
    status: WorkflowStatus = WorkflowStatus.RUNNING
    current_node_id: str | None = None
    completed_nodes: list[str] = field(default_factory=list)
    execution_context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def mark_node_complete(self, node_id: str, output_data: dict[str, Any] | None = None) -> None:
        if node_id not in self.completed_nodes:
            self.completed_nodes.append(node_id)
        if output_data:
            self.execution_context[node_id] = output_data
        self.updated_at = datetime.now(UTC)
