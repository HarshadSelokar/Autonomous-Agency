"""
Unit tests for Phase 25 Company, Bootstrap, Quota, and Cross-Company application services.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.company import (
    CompanyLifecycle,
    CompanyType,
    CompanyRole,
    RelationshipType,
    DataShareScope,
    DataShareStatus,
)
from src.domain.exceptions import (
    CompanyQuotaExceededError,
    CrossCompanyAccessDeniedError,
    InvalidLifecycleTransitionError,
)
from src.infrastructure.database import Base
import src.infrastructure.models.company_model
from src.infrastructure.repositories.company_repository import SQLAlchemyMultiCompanyRepository
from src.application.company_service import CompanyService
from src.application.company_bootstrap_service import CompanyBootstrapService
from src.application.company_quota_service import CompanyQuotaService
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
async def test_company_service_lifecycle_management(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)
    service = CompanyService(repo)

    company = await service.create_company("Apex Dynamics", "apex-dyn", "Autonomous logistics")
    assert company.lifecycle == CompanyLifecycle.PROPOSED

    # Transition lifecycle PROPOSED -> INITIALIZING -> ACTIVE
    init_comp = await service.transition_company_lifecycle(company.id, CompanyLifecycle.INITIALIZING)
    assert init_comp.lifecycle == CompanyLifecycle.INITIALIZING

    act_comp = await service.transition_company_lifecycle(company.id, CompanyLifecycle.ACTIVE)
    assert act_comp.lifecycle == CompanyLifecycle.ACTIVE

    # Adding members
    mem = await service.add_company_member(company.id, "user-bob", CompanyRole.MANAGER)
    assert mem.role == CompanyRole.MANAGER


@pytest.mark.asyncio
async def test_company_bootstrap_service(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)
    company_svc = CompanyService(repo)
    bootstrap_svc = CompanyBootstrapService(repo)

    tmpl = await bootstrap_svc.create_template(
        "Fintech Suite", "Template for financial AI companies", "FINTECH",
        ["Engineering", "Compliance", "Finance"], ["CTO", "ComplianceOfficer", "FinancialAnalyst"]
    )

    company = await company_svc.create_company("PayAI Corp", "pay-ai")
    bootstrapped = await bootstrap_svc.bootstrap_company(company.id, template_id=tmpl.id)

    assert bootstrapped.lifecycle == CompanyLifecycle.ACTIVE
    profile = await repo.get_company_profile(company.id)
    assert profile is not None
    assert profile.workforce_config["template_name"] == "Fintech Suite"


@pytest.mark.asyncio
async def test_company_quota_enforcement(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)
    quota_svc = CompanyQuotaService(repo)

    company_id = "comp-quota-test"

    # Set custom low quota
    quota = await quota_svc.get_or_create_quota(company_id)
    quota.max_concurrent_tasks = 2
    await repo.save_resource_quota(quota)

    # Check quota under limit -> passes
    await quota_svc.check_quota(company_id, "active_tasks", 2)

    # Increment active usage
    await quota_svc.increment_usage(company_id, "active_tasks", 2)

    # Requesting additional task breaches quota -> raises CompanyQuotaExceededError
    with pytest.raises(CompanyQuotaExceededError):
        await quota_svc.check_quota(company_id, "active_tasks", 1)


@pytest.mark.asyncio
async def test_cross_company_governance_and_access(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)
    cross_svc = CrossCompanyService(repo)

    comp_a = "comp-alpha"
    comp_b = "comp-beta"

    # Unrelated companies -> Cross-company access denied
    with pytest.raises(CrossCompanyAccessDeniedError):
        await cross_svc.verify_cross_company_access(comp_a, comp_b)

    # Establish partner relationship
    rel = await cross_svc.create_relationship(comp_a, comp_b, RelationshipType.PARTNER)
    assert rel.status == "ACTIVE"

    # Request data share
    req = await cross_svc.request_data_share(comp_a, comp_b, "Joint market analysis", DataShareScope.READ_ONLY)
    assert req.status == DataShareStatus.REQUESTED

    # Without governance approval -> Access denied
    with pytest.raises(CrossCompanyAccessDeniedError):
        await cross_svc.verify_cross_company_access(comp_a, comp_b)

    # Governance approves data share
    approved_req = await cross_svc.approve_data_share(req.id, "gov-auditor-01", governance_approval_id="gov-appr-ds-100")
    assert approved_req.status == DataShareStatus.APPROVED

    # Now cross-company access succeeds
    await cross_svc.verify_cross_company_access(comp_a, comp_b)
