"""
Pydantic API DTO Schemas for Task & Dependency Engine.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.task import BlockReason, TaskStatus
from src.domain.task_dependency import DependencyStatus, DependencyType


class TaskCreateRequest(BaseModel):
    plan_id: str
    title: str
    description: str
    objective_id: str | None = None
    work_item_id: str | None = None
    parent_task_id: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    priority: str = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: str
    plan_id: str
    title: str
    description: str
    objective_id: str | None = None
    work_item_id: str | None = None
    parent_task_id: str | None = None
    required_capabilities: list[str]
    priority: str
    status: TaskStatus
    assigned_employee_id: str | None = None
    assignment_id: str | None = None
    execution_run_id: str | None = None
    retry_count: int
    max_retries: int
    block_reasons: list[BlockReason]
    result: dict[str, Any] | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TaskDependencyCreateRequest(BaseModel):
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: DependencyType = DependencyType.BLOCKING
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskDependencyResponse(BaseModel):
    id: str
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: DependencyType
    status: DependencyStatus
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TaskClaimRequest(BaseModel):
    worker_id: str = "worker-1"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskReviewRequest(BaseModel):
    approved: bool
    reviewer_id: str = "manager-1"
    feedback: str | None = None


class TaskReworkRequest(BaseModel):
    reviewer_id: str = "manager-1"
    feedback: str = "Work requires revision."


class TaskCancelRequest(BaseModel):
    reason: str = "Cancelled by user or manager."


class SchedulerRunRequest(BaseModel):
    worker_id: str = "scheduler-1"
    plan_id: str | None = None
    max_tasks: int = 10


class SchedulerRunResponse(BaseModel):
    processed_tasks: list[TaskResponse]
    count: int
