"""
Integration Tests for Phase 25 Multi-Company & Multi-Tenant Security Isolation.

Verifies:
1. Strict tenant boundary isolation between distinct companies.
2. Cross-company access is denied by default.
3. Explicit relationship establishment and human governance approval requirements.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.company import (
    CompanyLifecycle,
    CompanyType,
    RelationshipType,
    DataShareScope,
    DataShareStatus,
    CompanyContext,
)
from src.domain.exceptions import (
    TenantIsolationViolationError,
    CrossCompanyAccessDeniedError,
)
from src.infrastructure.database import Base
import src.infrastructure.models.company_model
from src.infrastructure.repositories.company_repository import SQLAlchemyMultiCompanyRepository
from src.application.company_service import CompanyService
from src.application.cross_company_service import CrossCompanyService


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_isolation_context_verification():
    ctx_a = CompanyContext(company_id="comp-alpha")
    
    # Accessing company_alpha resource -> passes
    ctx_a.verify_company_access("comp-alpha", "financial_records")

    # Accessing company_beta resource -> raises TenantIsolationViolationError
    with pytest.raises(TenantIsolationViolationError):
        ctx_a.verify_company_access("comp-beta", "financial_records")


@pytest.mark.asyncio
async def test_cross_company_default_denial_and_governance_flow(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)
    company_svc = CompanyService(repo)
    cross_svc = CrossCompanyService(repo)

    # 1. Provision Company A & Company B
    comp_a = await company_svc.create_company("Alpha Tech", "alpha-tech", "Autonomous AI")
    comp_b = await company_svc.create_company("Beta Logistics", "beta-logistics", "Logistics AI")

    # 2. Denied by default
    with pytest.raises(CrossCompanyAccessDeniedError):
        await cross_svc.verify_cross_company_access(comp_a.id, comp_b.id)

    # 3. Establish Partner Relationship
    rel = await cross_svc.create_relationship(comp_a.id, comp_b.id, RelationshipType.PARTNER)
    assert rel.status == "ACTIVE"

    # 4. Request Data Share
    req = await cross_svc.request_data_share(
        source_company_id=comp_a.id,
        target_company_id=comp_b.id,
        purpose="Joint market analysis",
        data_scope=DataShareScope.READ_ONLY,
    )
    assert req.status == DataShareStatus.REQUESTED

    # 5. Access still denied prior to governance approval
    with pytest.raises(CrossCompanyAccessDeniedError):
        await cross_svc.verify_cross_company_access(comp_a.id, comp_b.id)

    # 6. Governance approves request
    approved = await cross_svc.approve_data_share(
        request_id=req.id,
        actor_id="human-auditor-1",
        governance_approval_id="gov-appr-ds-555",
    )
    assert approved.status == DataShareStatus.APPROVED

    # 7. Access now succeeds
    await cross_svc.verify_cross_company_access(comp_a.id, comp_b.id)
