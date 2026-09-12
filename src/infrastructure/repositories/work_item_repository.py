"""
SQLAlchemy Repository implementation for WorkItem domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repository import WorkItemRepositoryInterface
from src.domain.work_item import WorkItem
from src.infrastructure.models.work_item_model import (
    WorkItemModel,
    work_item_domain_to_model,
    work_item_model_to_domain,
)


class SQLAlchemyWorkItemRepository(WorkItemRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, work_item: WorkItem) -> WorkItem:
        model = work_item_domain_to_model(work_item)
        merged = await self.session.merge(model)
        await self.session.flush()
        return work_item_model_to_domain(merged)

    async def get_by_id(self, work_item_id: str) -> WorkItem | None:
        stmt = select(WorkItemModel).where(WorkItemModel.id == work_item_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return work_item_model_to_domain(model) if model else None

    async def list_by_plan_id(self, plan_id: str) -> list[WorkItem]:
        stmt = (
            select(WorkItemModel)
            .where(WorkItemModel.plan_id == plan_id)
            .order_by(WorkItemModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [work_item_model_to_domain(m) for m in models]
