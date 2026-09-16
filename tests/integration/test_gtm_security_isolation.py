"""
Integration tests for Phase 24 Commercial Governance, Customer Data Isolation, and Risk Controls.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.gtm import OpportunityStage, ProposalStatus, SupportPriority
from src.domain.exceptions import (
    PricingPolicyViolationError,
    UnauthorizedCommercialCommitmentError,
    CustomerDataIsolationError,
)
from src.infrastructure.database import Base
import src.infrastructure.models.gtm_model
import src.infrastructure.models.business_model
from src.infrastructure.repositories.gtm_repository import SQLAlchemyGTMRepository
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository
from src.application.product_management_service import ProductManagementService
from src.application.crm_sales_service import CRMSalesService
from src.application.customer_success_support_service import CustomerSuccessSupportService
from src.application.business_operations_service import BusinessOperationsService
from src.application.gtm_operations_service import GTMOperationsService


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
async def test_discount_governance_threshold_enforcement(async_session: AsyncSession):
    """Verifies that discounts <= 15% are auto-approved, while > 15% strictly require governance approval."""
    gtm_repo = SQLAlchemyGTMRepository(async_session)
    crm_svc = CRMSalesService(gtm_repo)

    lead = await crm_svc.create_lead("Target Corp", "Bob Vance", "bob@target.com")
    opp = await crm_svc.create_opportunity("Target Enterprise License", "prod-100", "sales-rep-1", 5000000, lead_id=lead.id)

    # 15% discount -> Pass
    prop_15 = await crm_svc.create_proposal(opp.id, "15 Percent Discount Proposal", "prod-100", 5000000, "sales-rep-1", discount_pct=15.0)
    sent_15 = await crm_svc.approve_and_send_proposal(prop_15.id, actor_id="sales-rep-1")
    assert sent_15.status == ProposalStatus.SENT

    # 15.1% discount -> Blocked without governance approval
    prop_15_1 = await crm_svc.create_proposal(opp.id, "15.1 Percent Discount Proposal", "prod-100", 5000000, "sales-rep-1", discount_pct=15.1)
    assert prop_15_1.status == ProposalStatus.APPROVAL_REQUIRED

    with pytest.raises(UnauthorizedCommercialCommitmentError):
        await crm_svc.approve_and_send_proposal(prop_15_1.id, actor_id="sales-rep-1", governance_approval_id=None)

    # Approved with governance approval ID -> Pass
    sent_15_1 = await crm_svc.approve_and_send_proposal(prop_15_1.id, actor_id="sales-rep-1", governance_approval_id="gov-appr-valid-151")
    assert sent_15_1.status == ProposalStatus.SENT


@pytest.mark.asyncio
async def test_invalid_discount_policy_violation(async_session: AsyncSession):
    """Verifies that negative discounts or discounts > 100% trigger PricingPolicyViolationError."""
    gtm_repo = SQLAlchemyGTMRepository(async_session)
    crm_svc = CRMSalesService(gtm_repo)

    lead = await crm_svc.create_lead("Alpha LLC", "Charlie Brown", "charlie@alpha.com")
    opp = await crm_svc.create_opportunity("Alpha Deal", "prod-100", "sales-rep-1", 1000000, lead_id=lead.id)

    # Discount > 100%
    with pytest.raises(PricingPolicyViolationError):
        await crm_svc.create_proposal(opp.id, "150% Off Proposal", "prod-100", 1000000, "sales-rep-1", discount_pct=150.0)

    # Discount < 0%
    with pytest.raises(PricingPolicyViolationError):
        await crm_svc.create_proposal(opp.id, "Negative Discount Proposal", "prod-100", 1000000, "sales-rep-1", discount_pct=-10.0)


@pytest.mark.asyncio
async def test_customer_tenant_data_isolation(async_session: AsyncSession):
    """Verifies strict customer data isolation across tenant boundaries."""
    gtm_repo = SQLAlchemyGTMRepository(async_session)
    cs_svc = CustomerSuccessSupportService(gtm_repo)

    cust_a = await cs_svc.create_customer_from_opportunity("Tenant A", "tenant-a.com")
    cust_b = await cs_svc.create_customer_from_opportunity("Tenant B", "tenant-b.com")

    # Same customer access -> Allowed
    cs_svc.verify_customer_access(requestor_customer_id=cust_a.id, target_customer_id=cust_a.id)

    # Cross customer access -> Raises CustomerDataIsolationError
    with pytest.raises(CustomerDataIsolationError) as exc_info:
        cs_svc.verify_customer_access(requestor_customer_id=cust_a.id, target_customer_id=cust_b.id)

    assert cust_a.id in str(exc_info.value)
    assert cust_b.id in str(exc_info.value)


@pytest.mark.asyncio
async def test_end_to_end_deal_won_revenue_governance(async_session: AsyncSession):
    """Verifies end-to-end commercial transition when closing a deal, connecting to Phase 23 billing & revenue."""
    gtm_repo = SQLAlchemyGTMRepository(async_session)
    biz_repo = SQLAlchemyBusinessRepository(async_session)
    biz_svc = BusinessOperationsService(biz_repo)
    gtm_ops_svc = GTMOperationsService(gtm_repo, business_service=biz_svc)

    lead = await gtm_ops_svc.crm_service.create_lead("Beta Corp", "David Miller", "david@beta.com")
    opp = await gtm_ops_svc.crm_service.create_opportunity("Beta Enterprise Contract", "prod-suite-01", "rep-1", 10000000, lead_id=lead.id)

    res = await gtm_ops_svc.execute_deal_won_and_onboard(opp.id, actor_id="mgr-1", governance_approval_id="gov-appr-deal-won-01")

    assert res["status"] == "WON_AND_ONBOARDING_INITIATED"
    assert res["customer_name"] == "Beta Enterprise Contract"
    assert res["invoice_id"] is not None
    assert res["payment_id"] is not None
    assert res["onboarding_id"] is not None
