"""
Pydantic Request and Response Schemas for AgentRun API Endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.domain.checkpoint import AgentCheckpoint
from src.domain.run import AgentRun, RunStatus
from src.domain.step import ExecutionStep, StepStatus, StepType


class CreateRunRequest(BaseModel):
    objective: str
    task_id: str | None = None
    response_schema: dict[str, Any] | None = None


class RunResponse(BaseModel):
    id: str
    agent_id: str
    objective: str
    status: RunStatus
    provider: str
    model: str
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    usage: dict[str, Any]
    result: dict[str, Any] | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, run: AgentRun) -> "RunResponse":
        return cls(
            id=run.id,
            agent_id=run.agent_id,
            objective=run.objective,
            status=run.status,
            provider=run.provider,
            model=run.model,
            started_at=run.started_at,
            completed_at=run.completed_at,
            failure_reason=run.failure_reason,
            usage=run.usage,
            result=run.result,
            metadata=run.metadata,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )


class StepResponse(BaseModel):
    id: str
    run_id: str
    step_number: int
    step_type: StepType
    status: StepStatus
    input_data: dict[str, Any]
    output_data: dict[str, Any] | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    metadata: dict[str, Any]

    @classmethod
    def from_domain(cls, step: ExecutionStep) -> "StepResponse":
        return cls(
            id=step.id,
            run_id=step.run_id,
            step_number=step.step_number,
            step_type=step.step_type,
            status=step.status,
            input_data=step.input_data,
            output_data=step.output_data,
            error_message=step.error_message,
            started_at=step.started_at,
            completed_at=step.completed_at,
            metadata=step.metadata,
        )


class CheckpointResponse(BaseModel):
    id: str
    run_id: str
    current_state: str
    current_step: int
    context_reference: dict[str, Any]
    output_so_far: dict[str, Any] | None
    metadata: dict[str, Any]
    timestamp: datetime

    @classmethod
    def from_domain(cls, chk: AgentCheckpoint) -> "CheckpointResponse":
        return cls(
            id=chk.id,
            run_id=chk.run_id,
            current_state=chk.current_state,
            current_step=chk.current_step,
            context_reference=chk.context_reference,
            output_so_far=chk.output_so_far,
            metadata=chk.metadata,
            timestamp=chk.timestamp,
        )
