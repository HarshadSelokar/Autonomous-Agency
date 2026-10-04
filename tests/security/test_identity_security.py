"""
Security tests for Identity Authorization Engine and RBAC Enforcer (Phase 33).
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.domain.identity import User, Organization, Membership, Role
from src.domain.exceptions import SecurityBoundaryViolationError
from src.infrastructure.database import Base, get_db_session
from src.infrastructure.repositories.identity_repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyMembershipRepository,
)
from src.application.authorization_service import AuthorizationService


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_authorization_service_enforcement(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    org_repo = SQLAlchemyOrganizationRepository(db_session)
    mem_repo = SQLAlchemyMembershipRepository(db_session)

    auth_service = AuthorizationService(user_repo=user_repo, membership_repo=mem_repo)

    # 1. Create User
    user = User(id="u1", tenant_id="t1", email="a@test.com", full_name="Alice")
    await user_repo.save(user)

    # 2. Create Org
    org = Organization(id="o1", tenant_id="t1", name="Engineering", slug="eng")
    await org_repo.save(org)

    # 3. Create Membership as EMPLOYEE
    membership = Membership(id="m1", tenant_id="t1", organization_id="o1", user_id="u1", role=Role.EMPLOYEE)
    await mem_repo.save(membership)

    # 4. Check permissions
    has_exec = await auth_service.check_permission("t1", "u1", "task:execute", organization_id="o1")
    assert has_exec is True

    has_tenant_write = await auth_service.check_permission("t1", "u1", "tenant:write", organization_id="o1")
    assert has_tenant_write is False

    # 5. Enforce unauthorized permission should raise SecurityBoundaryViolationError
    with pytest.raises(SecurityBoundaryViolationError):
        await auth_service.enforce_permission("t1", "u1", "tenant:write", organization_id="o1")
