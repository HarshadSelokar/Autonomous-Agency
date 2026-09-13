"""
SQLAlchemy Repositories for Tool, ToolExecution, ToolApproval, and ToolEvidence domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tool import (
    ApprovalStatus,
    ToolApproval,
    ToolDefinition,
    ToolEvidence,
    ToolExecution,
    ToolExecutionStatus,
)
from src.infrastructure.models.tool_model import (
    ToolApprovalModel,
    ToolEvidenceModel,
    ToolExecutionModel,
    ToolModel,
    tool_domain_to_model,
    tool_model_to_domain,
)


class SQLAlchemyToolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, tool: ToolDefinition) -> ToolDefinition:
        model = tool_domain_to_model(tool)
        merged = await self.session.merge(model)
        await self.session.flush()
        return tool_model_to_domain(merged)

    async def get_by_id(self, tool_id: str) -> ToolDefinition | None:
        stmt = select(ToolModel).where(ToolModel.id == tool_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return tool_model_to_domain(model) if model else None

    async def list_all(self) -> list[ToolDefinition]:
        stmt = select(ToolModel).order_by(ToolModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [tool_model_to_domain(m) for m in models]


class SQLAlchemyToolExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, execution: ToolExecution) -> ToolExecution:
        model = ToolExecutionModel(
            id=execution.id,
            request_id=execution.request_id,
            tool_id=execution.tool_id,
            tool_version=execution.tool_version,
            capability=execution.capability.value,
            actor_employee_id=execution.actor_employee_id,
            agent_id=execution.agent_id,
            agent_run_id=execution.agent_run_id,
            task_id=execution.task_id,
            workspace_id=execution.workspace_id,
            approval_id=execution.approval_id,
            status=execution.status.value,
            failure_reason=execution.failure_reason,
            execution_time_ms=execution.execution_time_ms,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return execution

    async def get_by_id(self, execution_id: str) -> ToolExecution | None:
        stmt = select(ToolExecutionModel).where(ToolExecutionModel.id == execution_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return ToolExecution(
            id=model.id,
            request_id=model.request_id,
            tool_id=model.tool_id,
            tool_version=model.tool_version,
            capability=model.capability,
            actor_employee_id=model.actor_employee_id,
            agent_id=model.agent_id,
            agent_run_id=model.agent_run_id,
            task_id=model.task_id,
            workspace_id=model.workspace_id,
            approval_id=model.approval_id,
            status=ToolExecutionStatus(model.status),
            failure_reason=model.failure_reason,
            execution_time_ms=model.execution_time_ms,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyToolApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, approval: ToolApproval) -> ToolApproval:
        model = ToolApprovalModel(
            id=approval.id,
            execution_id=approval.execution_id,
            tool_id=approval.tool_id,
            capability=approval.capability.value,
            requester_employee_id=approval.requester_employee_id,
            approver_employee_id=approval.approver_employee_id,
            status=approval.status.value,
            rationale=approval.rationale,
            created_at=approval.created_at,
            approved_at=approval.approved_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return approval

    async def get_by_id(self, approval_id: str) -> ToolApproval | None:
        stmt = select(ToolApprovalModel).where(ToolApprovalModel.id == approval_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return ToolApproval(
            id=model.id,
            execution_id=model.execution_id,
            tool_id=model.tool_id,
            capability=model.capability,
            requester_employee_id=model.requester_employee_id,
            approver_employee_id=model.approver_employee_id,
            status=ApprovalStatus(model.status),
            rationale=model.rationale,
            created_at=model.created_at,
            approved_at=model.approved_at,
        )
