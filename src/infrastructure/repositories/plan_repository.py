"""
SQLAlchemy Repository implementation for Plan domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.plan import Plan
from src.domain.repository import PlanRepositoryInterface
from src.infrastructure.models.plan_model import (
    PlanModel,
    plan_domain_to_model,
    plan_model_to_domain,
)
from src.infrastructure.models.work_item_model import WorkItemModel


class SQLAlchemyPlanRepository(PlanRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, plan: Plan) -> Plan:
        plan_model, work_item_models = plan_domain_to_model(plan)
        merged_plan = await self.session.merge(plan_model)
        saved_work_items: list[WorkItemModel] = []
        for wi_model in work_item_models:
            merged_wi = await self.session.merge(wi_model)
            saved_work_items.append(merged_wi)
        await self.session.flush()
        return plan_model_to_domain(merged_plan, saved_work_items)

    async def get_by_id(self, plan_id: str) -> Plan | None:
        stmt = select(PlanModel).where(PlanModel.id == plan_id)
        result = await self.session.execute(stmt)
        plan_model = result.scalar_one_or_none()
        if plan_model is None:
            return None

        wi_stmt = (
            select(WorkItemModel)
            .where(WorkItemModel.plan_id == plan_id)
            .order_by(WorkItemModel.created_at.asc())
        )
        wi_res = await self.session.execute(wi_stmt)
        wi_models = list(wi_res.scalars().all())

        return plan_model_to_domain(plan_model, wi_models)

    async def get_by_objective_id(self, objective_id: str) -> Plan | None:
        stmt = select(PlanModel).where(PlanModel.objective_id == objective_id)
        result = await self.session.execute(stmt)
        plan_model = result.scalar_one_or_none()
        if plan_model is None:
            return None

        wi_stmt = (
            select(WorkItemModel)
            .where(WorkItemModel.plan_id == plan_model.id)
            .order_by(WorkItemModel.created_at.asc())
        )
        wi_res = await self.session.execute(wi_stmt)
        wi_models = list(wi_res.scalars().all())

        return plan_model_to_domain(plan_model, wi_models)
