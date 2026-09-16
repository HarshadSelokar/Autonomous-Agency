"""
Pydantic API Schemas for Phase 7 Memory Management.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateMemoryRequest(BaseModel):
    memory_type: str = Field(..., description="WORKING, EPISODIC, SEMANTIC, PROCEDURAL, ORGANIZATIONAL")
    scope: str = Field(..., description="RUN, TASK, EMPLOYEE, PROJECT, DEPARTMENT, COMPANY")
    owner_id: str
    content: str
    summary: str | None = None
    authority: str = "GENERATED"
    confidence: float = 0.5
    provenance: str = "AGENT_RUN"
    source_id: str | None = None
    task_id: str | None = None
    employee_id: str | None = None
    agent_run_id: str | None = None
    meeting_id: str | None = None
    decision_id: str | None = None
    artifact_id: str | None = None


class PromoteMemoryRequest(BaseModel):
    actor_employee_id: str
    target_authority: str = Field(..., description="CONFIRMED, AUTHORITATIVE")


class ConfirmMemoryRequest(BaseModel):
    actor_employee_id: str


class MemoryResponse(BaseModel):
    id: str
    memory_type: str
    scope: str
    owner_id: str
    content: str
    summary: str | None = None
    authority: str
    confidence: float
    provenance: str
    status: str
    task_id: str | None = None
    decision_id: str | None = None
    artifact_id: str | None = None
    created_at: datetime
