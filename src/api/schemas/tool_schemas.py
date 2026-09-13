"""
Pydantic API Schemas for Phase 8 Tool Management, Executions, Approvals, and Evidence.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CreateToolRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=256)
    description: str
    version: str = "1.0.0"
    category: str = "INTEGRATION"
    capabilities: list[str]
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"
    permission_mode: str = "AUTO"
    provider_name: str = "internal"


class ToolResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    category: str
    capabilities: list[str]
    risk_level: str
    permission_mode: str
    status: str


class ExecuteToolRequest(BaseModel):
    tool_id: str
    tool_version: str = "1.0.0"
    capability: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    employee_id: str
    agent_id: str
    agent_run_id: str
    task_id: str | None = None
    workspace_id: str | None = None
    purpose: str = ""


class ToolExecutionResponse(BaseModel):
    id: str
    request_id: str
    tool_id: str
    capability: str
    status: str
    actor_employee_id: str
    approval_id: str | None = None
    failure_reason: str | None = None
    execution_time_ms: float | None = None
    output: dict[str, Any] | None = None


class ApproveToolRequest(BaseModel):
    approver_employee_id: str
    rationale: str | None = None


class ToolApprovalResponse(BaseModel):
    id: str
    execution_id: str
    tool_id: str
    capability: str
    requester_employee_id: str
    approver_employee_id: str | None = None
    status: str
    rationale: str | None = None
    created_at: datetime
    approved_at: datetime | None = None
