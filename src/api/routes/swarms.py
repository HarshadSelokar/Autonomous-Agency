"""
FastAPI Routes for Phase 22 Multi-Agent Swarms.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.swarm_service import SwarmService
from src.domain.exceptions import SwarmBudgetExceededError, SwarmDepthExceededError, SwarmNotFoundError, SwarmValidationError
from src.domain.swarm import CoordinationMode, SwarmMessageType, SwarmStatus
from src.infrastructure.database import get_db
from src.infrastructure.repositories.swarm_repository import SQLAlchemySwarmRepository

router = APIRouter(prefix="/swarms", tags=["swarms"])


class CreateSwarmRequest(BaseModel):
    parent_task_id: str = Field(..., description="ID of authoritative parent task")
    name: str = Field(..., description="Name of the swarm")
    purpose: str = Field(..., description="Purpose or objective description of the swarm")
    manager_id: str = Field(..., description="ID of manager employee governing the swarm")
    coordination_mode: str = Field(default="PARALLEL", description="Topology coordination mode")
    depth: int = Field(default=1, description="Swarm nesting depth")
    max_agents: int = Field(default=10, description="Max allowed member count")
    custom_budget: dict[str, Any] | None = Field(default=None, description="Resource budget overrides")


class FormSwarmRequest(BaseModel):
    task_title: str
    task_description: str
    required_capabilities: list[str]
    available_employees: list[dict[str, str]] | None = None


class ExecuteSubtaskRequest(BaseModel):
    member_id: str
    objective: str
    subtask_id: str | None = None
    duration_seconds: int = 10
    model_cost: float = 0.5
    tool_calls: int = 2
    tokens: int = 1500
    output_payload: dict[str, Any] | None = None


class SendSwarmMessageRequest(BaseModel):
    sender_id: str
    recipient_id: str | None = None
    message_type: str = "STATUS_UPDATE"
    payload: dict[str, Any]
    task_id: str | None = None


class CompleteSwarmRequest(BaseModel):
    member_results: dict[str, Any]
    strategy: str = "DETERMINISTIC_MERGE"


def get_swarm_service(db: AsyncSession = Depends(get_db)) -> SwarmService:
    repo = SQLAlchemySwarmRepository(db)
    return SwarmService(swarm_repo=repo)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_swarm(
    req: CreateSwarmRequest,
    service: SwarmService = Depends(get_swarm_service),
):
    try:
        mode = CoordinationMode(req.coordination_mode.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid coordination_mode '{req.coordination_mode}'")

    try:
        swarm = await service.create_swarm(
            parent_task_id=req.parent_task_id,
            name=req.name,
            purpose=req.purpose,
            manager_id=req.manager_id,
            coordination_mode=mode,
            depth=req.depth,
            max_agents=req.max_agents,
            custom_budget=req.custom_budget,
        )
        return {"swarm_id": swarm.id, "status": swarm.status.value, "code": swarm.code}
    except (SwarmDepthExceededError, SwarmValidationError) as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("")
async def list_swarms(
    parent_task_id: str | None = None,
    service: SwarmService = Depends(get_swarm_service),
):
    if parent_task_id:
        swarms = await service.swarm_repo.list_by_parent_task(parent_task_id)
    else:
        swarms = await service.swarm_repo.list_all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "parent_task_id": s.parent_task_id,
            "status": s.status.value,
            "coordination_mode": s.coordination_mode.value,
            "member_count": len(s.members),
            "created_at": s.created_at.isoformat(),
        }
        for s in swarms
    ]


@router.get("/{swarm_id}")
async def get_swarm_details(
    swarm_id: str,
    service: SwarmService = Depends(get_swarm_service),
):
    swarm = await service.swarm_repo.get_by_id(swarm_id)
    if swarm is None:
        raise HTTPException(status_code=404, detail=f"Swarm '{swarm_id}' not found")
    budget = await service.swarm_repo.get_budget(swarm_id)

    return {
        "id": swarm.id,
        "name": swarm.name,
        "code": swarm.code,
        "parent_task_id": swarm.parent_task_id,
        "purpose": swarm.purpose,
        "manager_id": swarm.manager_id,
        "status": swarm.status.value,
        "coordination_mode": swarm.coordination_mode.value,
        "depth": swarm.depth,
        "concurrency_limit": swarm.concurrency_limit,
        "max_agents": swarm.max_agents,
        "members": [
            {
                "id": m.id,
                "employee_id": m.employee_id,
                "agent_id": m.agent_id,
                "role": m.role,
                "capability": m.capability,
                "status": m.status.value,
                "assigned_task_id": m.assigned_task_id,
            }
            for m in swarm.members
        ],
        "budget": {
            "max_execution_time_seconds": budget.max_execution_time_seconds if budget else 3600,
            "current_execution_time_seconds": budget.current_execution_time_seconds if budget else 0,
            "max_model_cost": budget.max_model_cost if budget else 50.0,
            "current_model_cost": budget.current_model_cost if budget else 0.0,
            "max_tool_calls": budget.max_tool_calls if budget else 200,
            "current_tool_calls": budget.current_tool_calls if budget else 0,
        }
        if budget
        else None,
        "created_at": swarm.created_at.isoformat(),
    }


@router.post("/{swarm_id}/plan")
async def plan_swarm(
    swarm_id: str,
    req: FormSwarmRequest,
    service: SwarmService = Depends(get_swarm_service),
):
    try:
        swarm = await service.plan_and_form_swarm(
            swarm_id=swarm_id,
            task_title=req.task_title,
            task_description=req.task_description,
            required_capabilities=req.required_capabilities,
            available_employees=req.available_employees,
        )
        return {"swarm_id": swarm.id, "status": swarm.status.value, "members_formed": len(swarm.members)}
    except SwarmNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/{swarm_id}/start")
async def start_swarm(
    swarm_id: str,
    service: SwarmService = Depends(get_swarm_service),
):
    try:
        swarm = await service.start_swarm(swarm_id)
        return {"swarm_id": swarm.id, "status": swarm.status.value}
    except SwarmNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/{swarm_id}/execute-subtask")
async def execute_subtask(
    swarm_id: str,
    req: ExecuteSubtaskRequest,
    service: SwarmService = Depends(get_swarm_service),
):
    try:
        res = await service.execute_member_subtask(
            swarm_id=swarm_id,
            member_id=req.member_id,
            objective=req.objective,
            subtask_id=req.subtask_id,
            duration_seconds=req.duration_seconds,
            model_cost=req.model_cost,
            tool_calls=req.tool_calls,
            tokens=req.tokens,
            output_payload=req.output_payload,
        )
        return {"status": "SUCCESS", "result": res}
    except SwarmNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except SwarmBudgetExceededError as err:
        raise HTTPException(status_code=429, detail=str(err))


@router.post("/{swarm_id}/messages")
async def send_swarm_message(
    swarm_id: str,
    req: SendSwarmMessageRequest,
    service: SwarmService = Depends(get_swarm_service),
):
    try:
        msg_type = SwarmMessageType(req.message_type.upper())
    except ValueError:
        msg_type = SwarmMessageType.STATUS_UPDATE

    msg = await service.send_inter_agent_message(
        swarm_id=swarm_id,
        sender_id=req.sender_id,
        recipient_id=req.recipient_id,
        message_type=msg_type,
        payload=req.payload,
        task_id=req.task_id,
    )
    return {"message_id": msg.id, "correlation_id": msg.correlation_id}


@router.get("/{swarm_id}/messages")
async def list_swarm_messages(
    swarm_id: str,
    service: SwarmService = Depends(get_swarm_service),
):
    messages = await service.swarm_repo.list_messages_by_swarm(swarm_id)
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "recipient_id": m.recipient_id,
            "message_type": m.message_type.value,
            "payload": m.payload,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/{swarm_id}/complete")
async def complete_swarm(
    swarm_id: str,
    req: CompleteSwarmRequest,
    service: SwarmService = Depends(get_swarm_service),
):
    try:
        result = await service.complete_swarm(swarm_id, req.member_results, req.strategy)
        return {"swarm_id": swarm_id, "result_id": result.id, "verification_status": result.verification_status}
    except SwarmNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/{swarm_id}/pause")
async def pause_swarm(swarm_id: str, service: SwarmService = Depends(get_swarm_service)):
    swarm = await service.pause_swarm(swarm_id)
    return {"swarm_id": swarm.id, "status": swarm.status.value}


@router.post("/{swarm_id}/resume")
async def resume_swarm(swarm_id: str, service: SwarmService = Depends(get_swarm_service)):
    swarm = await service.resume_swarm(swarm_id)
    return {"swarm_id": swarm.id, "status": swarm.status.value}


@router.post("/{swarm_id}/cancel")
async def cancel_swarm(swarm_id: str, service: SwarmService = Depends(get_swarm_service)):
    swarm = await service.cancel_swarm(swarm_id)
    return {"swarm_id": swarm.id, "status": swarm.status.value}


@router.get("/{swarm_id}/metrics")
async def get_swarm_metrics(swarm_id: str, service: SwarmService = Depends(get_swarm_service)):
    metrics = service.observability.get_metrics()
    budget = await service.swarm_repo.get_budget(swarm_id)
    return {
        "swarm_id": swarm_id,
        "global_metrics": metrics,
        "budget": {
            "current_execution_time_seconds": budget.current_execution_time_seconds if budget else 0,
            "current_model_cost": budget.current_model_cost if budget else 0.0,
            "current_tool_calls": budget.current_tool_calls if budget else 0,
        }
        if budget
        else None,
    }
