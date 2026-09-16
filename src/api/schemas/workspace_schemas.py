"""
Pydantic API Schemas for Phase 7 Workspace Management.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    workspace_type: str = Field(..., description="TASK, PROJECT, EMPLOYEE, AGENT, SHARED")
    owner_id: str
    task_id: str | None = None
    project_id: str | None = None
    employee_id: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    workspace_type: str
    owner_id: str
    status: str
    task_id: str | None = None
    project_id: str | None = None
    employee_id: str | None = None
    created_at: datetime
