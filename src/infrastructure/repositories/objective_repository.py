"""
SQLAlchemy Repository implementation for Objective domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.objective import Objective
from src.domain.repository import ObjectiveRepositoryInterface
from src.infrastructure.models.objective_model import (
    ObjectiveModel,
    objective_domain_to_model,
    objective_model_to_domain,
)


class SQLAlchemyObjectiveRepository(ObjectiveRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, objective: Objective) -> Objective:
        model = objective_domain_to_model(objective)
        merged = await self.session.merge(model)
        await self.session.flush()
        return objective_model_to_domain(merged)

    async def get_by_id(self, objective_id: str) -> Objective | None:
        stmt = select(ObjectiveModel).where(ObjectiveModel.id == objective_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return objective_model_to_domain(model) if model else None

    async def list_all(self) -> list[Objective]:
        stmt = select(ObjectiveModel).order_by(ObjectiveModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [objective_model_to_domain(m) for m in models]

    async def list_by_manager_id(self, manager_id: str) -> list[Objective]:
        stmt = (
            select(ObjectiveModel)
            .where(ObjectiveModel.manager_id == manager_id)
            .order_by(ObjectiveModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [objective_model_to_domain(m) for m in models]
