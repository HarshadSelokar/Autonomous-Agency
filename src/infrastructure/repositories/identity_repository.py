"""
SQLAlchemy Repositories for User, Organization, and Membership domain persistence (Phase 33).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.identity import User, Organization, Membership
from src.infrastructure.models.identity_model import (
    UserModel,
    OrganizationModel,
    MembershipModel,
    user_domain_to_model,
    user_model_to_domain,
    organization_domain_to_model,
    organization_model_to_domain,
    membership_domain_to_model,
    membership_model_to_domain,
)


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, user: User) -> User:
        model = user_domain_to_model(user)
        merged = await self.session.merge(model)
        await self.session.flush()
        return user_model_to_domain(merged)

    async def get_by_id(self, user_id: str) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return user_model_to_domain(model) if model else None

    async def get_by_email(self, tenant_id: str, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.tenant_id == tenant_id, UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return user_model_to_domain(model) if model else None

    async def find_by_email(self, email: str) -> list[User]:
        """All users with this email across tenants (emails are unique per tenant only)."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return [user_model_to_domain(m) for m in result.unique().scalars().all()]

    async def list_by_tenant(self, tenant_id: str) -> list[User]:
        stmt = select(UserModel).where(UserModel.tenant_id == tenant_id).order_by(UserModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [user_model_to_domain(m) for m in models]


class SQLAlchemyOrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, org: Organization) -> Organization:
        model = organization_domain_to_model(org)
        merged = await self.session.merge(model)
        await self.session.flush()
        return organization_model_to_domain(merged)

    async def get_by_id(self, org_id: str) -> Organization | None:
        stmt = select(OrganizationModel).where(OrganizationModel.id == org_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return organization_model_to_domain(model) if model else None

    async def list_by_tenant(self, tenant_id: str) -> list[Organization]:
        stmt = select(OrganizationModel).where(OrganizationModel.tenant_id == tenant_id).order_by(OrganizationModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [organization_model_to_domain(m) for m in models]


class SQLAlchemyMembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, membership: Membership) -> Membership:
        model = membership_domain_to_model(membership)
        merged = await self.session.merge(model)
        await self.session.flush()
        return membership_model_to_domain(merged)

    async def get_membership(self, tenant_id: str, org_id: str, user_id: str) -> Membership | None:
        stmt = select(MembershipModel).where(
            MembershipModel.tenant_id == tenant_id,
            MembershipModel.organization_id == org_id,
            MembershipModel.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return membership_model_to_domain(model) if model else None

    async def list_by_user(self, user_id: str) -> list[Membership]:
        stmt = select(MembershipModel).where(MembershipModel.user_id == user_id)
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [membership_model_to_domain(m) for m in models]
