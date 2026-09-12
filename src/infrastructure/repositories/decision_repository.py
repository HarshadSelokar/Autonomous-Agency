"""
SQLAlchemy Repository implementation for ManagerDecision domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.decision import ManagerDecision
from src.domain.repository import DecisionRepositoryInterface
from src.infrastructure.models.decision_model import (
    ManagerDecisionModel,
    decision_domain_to_model,
    decision_model_to_domain,
)


class SQLAlchemyDecisionRepository(DecisionRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, decision: ManagerDecision) -> ManagerDecision:
        model = decision_domain_to_model(decision)
        merged = await self.session.merge(model)
        await self.session.flush()
        return decision_model_to_domain(merged)

    async def get_by_id(self, decision_id: str) -> ManagerDecision | None:
        stmt = select(ManagerDecisionModel).where(ManagerDecisionModel.id == decision_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return decision_model_to_domain(model) if model else None

    async def list_by_objective_id(self, objective_id: str) -> list[ManagerDecision]:
        stmt = (
            select(ManagerDecisionModel)
            .where(ManagerDecisionModel.objective_id == objective_id)
            .order_by(ManagerDecisionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [decision_model_to_domain(m) for m in models]
