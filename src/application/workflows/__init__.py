"""
Canonical platform operating workflows package.
"""

from src.application.workflows.platform_workflows import (
    PlatformWorkflowEngine,
    WorkflowCategory,
    WorkflowExecutionRecord,
    WorkflowState,
)

__all__ = [
    "PlatformWorkflowEngine",
    "WorkflowCategory",
    "WorkflowExecutionRecord",
    "WorkflowState",
]
