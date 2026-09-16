"""
FastAPI Routes for Phase 8 Tool Management, Executions, Approvals, and Evidence.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.tool_schemas import (
    ApproveToolRequest,
    CreateToolRequest,
    ExecuteToolRequest,
    ToolApprovalResponse,
    ToolExecutionResponse,
    ToolResponse,
)
from src.application.tool_approval_service import ToolApprovalService, UnauthorizedApprovalError
from src.application.tool_execution_pipeline import ToolExecutionPipeline
from src.application.tool_registry import ToolRegistry
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolRequest,
    ToolRiskLevel,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.tool_repository import (
    SQLAlchemyToolApprovalRepository,
    SQLAlchemyToolExecutionRepository,
    SQLAlchemyToolRepository,
)

router = APIRouter(tags=["Tools"])

# Global Tool Registry Singleton for API server
global_tool_registry = ToolRegistry()


def _to_tool_response(tool: ToolDefinition) -> ToolResponse:
    return ToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        version=tool.version,
        category=tool.category.value,
        capabilities=[c.value for c in tool.capabilities],
        risk_level=tool.risk_level.value,
        permission_mode=tool.permission_mode.value,
        status=tool.status.value,
    )


@router.post("/tools", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def register_tool(
    payload: CreateToolRequest,
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    tool_repo = SQLAlchemyToolRepository(db)
    caps = [ToolCapability(c.upper()) for c in payload.capabilities]
    tool = ToolDefinition(
        id=payload.id,
        name=payload.name,
        description=payload.description,
        version=payload.version,
        category=ToolCategory(payload.category.upper()),
        capabilities=caps,
        input_schema=payload.input_schema,
        output_schema=payload.output_schema,
        risk_level=ToolRiskLevel(payload.risk_level.upper()),
        permission_mode=PermissionMode(payload.permission_mode.upper()),
        provider_name=payload.provider_name,
    )
    saved = await tool_repo.save(tool)
    global_tool_registry.register(saved)
    await db.commit()
    return _to_tool_response(saved)


@router.get("/tools", response_model=list[ToolResponse])
async def list_tools(
    db: AsyncSession = Depends(get_db),
) -> list[ToolResponse]:
    tool_repo = SQLAlchemyToolRepository(db)
    tools = await tool_repo.list_all()
    for t in tools:
        global_tool_registry.register(t)
    return [_to_tool_response(t) for t in tools]


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    tool_repo = SQLAlchemyToolRepository(db)
    tool = await tool_repo.get_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool '{tool_id}' not found.")
    return _to_tool_response(tool)


@router.post("/tool-executions", response_model=ToolExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_tool(
    payload: ExecuteToolRequest,
    db: AsyncSession = Depends(get_db),
) -> ToolExecutionResponse:
    emp_repo = SQLAlchemyEmployeeRepository(db)
    exec_repo = SQLAlchemyToolExecutionRepository(db)
    appr_repo = SQLAlchemyToolApprovalRepository(db)

    approval_service = ToolApprovalService(employee_repo=emp_repo, approval_repo=appr_repo)
    pipeline = ToolExecutionPipeline(
        registry=global_tool_registry,
        approval_service=approval_service,
        employee_repo=emp_repo,
        execution_repo=exec_repo,
    )

    req = ToolRequest(
        id=f"req-{uuid.uuid4().hex[:8]}",
        tool_id=payload.tool_id,
        tool_version=payload.tool_version,
        requested_capability=ToolCapability(payload.capability.upper()),
        arguments=payload.arguments,
        employee_id=payload.employee_id,
        agent_id=payload.agent_id,
        agent_run_id=payload.agent_run_id,
        task_id=payload.task_id,
        workspace_id=payload.workspace_id,
        purpose=payload.purpose,
    )

    res = await pipeline.execute_tool_request(req)
    await db.commit()

    return ToolExecutionResponse(
        id=res.execution_id,
        request_id=req.id,
        tool_id=payload.tool_id,
        capability=payload.capability,
        status=res.status.value,
        actor_employee_id=payload.employee_id,
        approval_id=res.output.get("approval_id") if isinstance(res.output, dict) else None,
        failure_reason=res.error_message,
        execution_time_ms=res.execution_time_ms,
        output=res.output,
    )


@router.post("/tool-approvals/{approval_id}/approve", response_model=ToolApprovalResponse)
async def approve_tool_execution(
    approval_id: str,
    payload: ApproveToolRequest,
    db: AsyncSession = Depends(get_db),
) -> ToolApprovalResponse:
    emp_repo = SQLAlchemyEmployeeRepository(db)
    appr_repo = SQLAlchemyToolApprovalRepository(db)
    approval_service = ToolApprovalService(employee_repo=emp_repo, approval_repo=appr_repo)

    try:
        appr = await approval_service.approve_request(
            approval_id=approval_id,
            approver_employee_id=payload.approver_employee_id,
            rationale=payload.rationale,
        )
        await db.commit()
        return ToolApprovalResponse(
            id=appr.id,
            execution_id=appr.execution_id,
            tool_id=appr.tool_id,
            capability=appr.capability.value,
            requester_employee_id=appr.requester_employee_id,
            approver_employee_id=appr.approver_employee_id,
            status=appr.status.value,
            rationale=appr.rationale,
            created_at=appr.created_at,
            approved_at=appr.approved_at,
        )
    except UnauthorizedApprovalError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))


@router.post("/tool-approvals/{approval_id}/reject", response_model=ToolApprovalResponse)
async def reject_tool_execution(
    approval_id: str,
    payload: ApproveToolRequest,
    db: AsyncSession = Depends(get_db),
) -> ToolApprovalResponse:
    emp_repo = SQLAlchemyEmployeeRepository(db)
    appr_repo = SQLAlchemyToolApprovalRepository(db)
    approval_service = ToolApprovalService(employee_repo=emp_repo, approval_repo=appr_repo)

    appr = await approval_service.reject_request(
        approval_id=approval_id,
        approver_employee_id=payload.approver_employee_id,
        rationale=payload.rationale,
    )
    await db.commit()

    return ToolApprovalResponse(
        id=appr.id,
        execution_id=appr.execution_id,
        tool_id=appr.tool_id,
        capability=appr.capability.value,
        requester_employee_id=appr.requester_employee_id,
        approver_employee_id=appr.approver_employee_id,
        status=appr.status.value,
        rationale=appr.rationale,
        created_at=appr.created_at,
        approved_at=appr.approved_at,
    )
