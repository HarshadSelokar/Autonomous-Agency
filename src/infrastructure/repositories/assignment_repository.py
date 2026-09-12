"""
SQLAlchemy Repository implementation for Assignment domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.assignment import Assignment
from src.domain.repository import AssignmentRepositoryInterface
from src.infrastructure.models.assignment_model import (
    AssignmentModel,
    assignment_domain_to_model,
    assignment_model_to_domain,
)


class SQLAlchemyAssignmentRepository(AssignmentRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, assignment: Assignment) -> Assignment:
        model = assignment_domain_to_model(assignment)
        merged = await self.session.merge(model)
        await self.session.flush()
        return assignment_model_to_domain(merged)

    async def get_by_id(self, assignment_id: str) -> Assignment | None:
        stmt = select(AssignmentModel).where(AssignmentModel.id == assignment_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return assignment_model_to_domain(model) if model else None

    async def list_by_work_item_id(self, work_item_id: str) -> list[Assignment]:
        stmt = (
            select(AssignmentModel)
            .where(AssignmentModel.work_item_id == work_item_id)
            .order_by(AssignmentModel.assigned_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [assignment_model_to_domain(m) for m in models]
