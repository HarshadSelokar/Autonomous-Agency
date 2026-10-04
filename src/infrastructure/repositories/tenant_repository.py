"""
SQLAlchemy Repository implementation for Tenant domain persistence (Phase 32).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tenant import Tenant
from src.infrastructure.models.tenant_model import (
    TenantModel,
    tenant_domain_to_model,
    tenant_model_to_domain,
)


class SQLAlchemyTenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, tenant: Tenant) -> Tenant:
        model = tenant_domain_to_model(tenant)
        merged = await self.session.merge(model)
        await self.session.flush()
        return tenant_model_to_domain(merged)

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return tenant_model_to_domain(model) if model else None

    async def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(TenantModel).where(TenantModel.slug == slug)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return tenant_model_to_domain(model) if model else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Tenant]:
        stmt = (
            select(TenantModel)
            .order_by(TenantModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [tenant_model_to_domain(m) for m in models]

    async def delete(self, tenant_id: str) -> bool:
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False
