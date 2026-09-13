"""
SQLAlchemy Repository implementation for MemoryEntry domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.memory import MemoryEntry, MemoryStatus
from src.domain.repository import MemoryRepositoryInterface
from src.infrastructure.models.memory_model import (
    MemoryModel,
    memory_domain_to_model,
    memory_model_to_domain,
)


class SQLAlchemyMemoryRepository(MemoryRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, memory: MemoryEntry) -> MemoryEntry:
        model = memory_domain_to_model(memory)
        merged = await self.session.merge(model)
        await self.session.flush()
        return memory_model_to_domain(merged)

    async def get_by_id(self, memory_id: str) -> MemoryEntry | None:
        stmt = select(MemoryModel).where(MemoryModel.id == memory_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return memory_model_to_domain(model) if model else None

    async def list_by_owner(self, owner_id: str) -> list[MemoryEntry]:
        stmt = (
            select(MemoryModel)
            .where(MemoryModel.owner_id == owner_id, MemoryModel.status == MemoryStatus.ACTIVE.value)
            .order_by(MemoryModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [memory_model_to_domain(m) for m in models]

    async def list_all(self) -> list[MemoryEntry]:
        stmt = select(MemoryModel).order_by(MemoryModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [memory_model_to_domain(m) for m in models]
