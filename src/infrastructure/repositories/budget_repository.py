"""
SQLAlchemy Repository implementation for Budget and Cost persistence (Phase 35).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.budget import Budget, CostRecord
from src.infrastructure.models.budget_model import (
    ResourceBudgetModel,
    CostRecordModel,
    budget_domain_to_model,
    budget_model_to_domain,
)


class SQLAlchemyBudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, budget: Budget) -> Budget:
        model = budget_domain_to_model(budget)
        merged = await self.session.merge(model)
        await self.session.flush()
        return budget_model_to_domain(merged)

    async def get_by_id(self, budget_id: str) -> Budget | None:
        stmt = select(ResourceBudgetModel).where(ResourceBudgetModel.id == budget_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return budget_model_to_domain(model) if model else None

    async def get_by_tenant_and_project(
        self, tenant_id: str, project_id: str | None = None, budget_type: str = "COST"
    ) -> Budget | None:
        stmt = select(ResourceBudgetModel).where(
            ResourceBudgetModel.tenant_id == tenant_id,
            ResourceBudgetModel.project_id == project_id,
            ResourceBudgetModel.budget_type == budget_type,
        )
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return budget_model_to_domain(model) if model else None

    async def save_cost_record(self, record: CostRecord) -> CostRecord:
        model = CostRecordModel(
            id=record.id,
            tenant_id=record.tenant_id,
            project_id=record.project_id,
            task_id=record.task_id,
            agent_id=record.agent_id,
            model_name=record.model_name,
            tokens_prompt=record.tokens_prompt,
            tokens_completion=record.tokens_completion,
            estimated_cost=record.estimated_cost,
            created_at=record.created_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return record
