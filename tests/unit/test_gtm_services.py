"""
Unit tests for Phase 24 Product, Customer & GTM application services.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.gtm import (
    OpportunityStage,
    ProposalStatus,
    SupportPriority,
)
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
async def test_product_management_service_feedback_loop(async_session: AsyncSession):
    repo = SQLAlchemyGTMRepository(async_session)
    service = ProductManagementService(repo)

    prod = await service.create_product("Swarm Orchestrator", "SWARM-01", "AI Agent Coordinator", "emp-1", 500000)
    assert prod.code == "SWARM-01"

    fb = await service.record_customer_feedback(prod.id, "cust-1", "Add real-time UI dashboard", "We need real-time visualization of agent swarms.")
    assert fb.product_id == prod.id

    req = await service.synthesize_feedback_to_requirement(fb.id, "Real-Time Swarm Dashboard", "As a user I want real-time swarm visualization.", "HIGH", "task-100")
    assert req.source_feedback_id == fb.id
    assert req.task_id == "task-100"


@pytest.mark.asyncio
async def test_crm_sales_proposal_discount_governance(async_session: AsyncSession):
    repo = SQLAlchemyGTMRepository(async_session)
    service = CRMSalesService(repo)

    lead = await service.create_lead("Acme Corp", "John Doe", "john@acme.com")
    opp = await service.create_opportunity("Acme Enterprise Deal", "prod-100", "sales-rep-1", 10000000, lead_id=lead.id)

    # 10% discount proposal passes auto-approval
    prop10 = await service.create_proposal(opp.id, "Standard Proposal", "prod-100", 10000000, "sales-rep-1", discount_pct=10.0)
    sent_prop10 = await service.approve_and_send_proposal(prop10.id, actor_id="sales-rep-1")
    assert sent_prop10.status == ProposalStatus.SENT

    # 25% discount proposal requires explicit governance approval
    prop25 = await service.create_proposal(opp.id, "High Discount Proposal", "prod-100", 10000000, "sales-rep-1", discount_pct=25.0)
    with pytest.raises(UnauthorizedCommercialCommitmentError):
        await service.approve_and_send_proposal(prop25.id, actor_id="sales-rep-1", governance_approval_id=None)

    # With governance approval, 25% discount proposal succeeds
    approved_prop25 = await service.approve_and_send_proposal(prop25.id, actor_id="sales-rep-1", governance_approval_id="gov-app-25")
    assert approved_prop25.status == ProposalStatus.SENT


@pytest.mark.asyncio
async def test_customer_isolation_and_support_flow(async_session: AsyncSession):
    repo = SQLAlchemyGTMRepository(async_session)
    service = CustomerSuccessSupportService(repo)

    # Test customer data isolation
    with pytest.raises(CustomerDataIsolationError):
        service.verify_customer_access("cust-A", "cust-B")

    cust = await service.create_customer_from_opportunity("Global Corp", "global.com")
    case = await service.create_support_case(cust.id, "Integration Error", "API returns 500", SupportPriority.HIGH)
    assert case.customer_id == cust.id

    resolved = await service.resolve_support_case(case.id, "supp-agent-1", "Fixed API rate limit configuration.")
    assert resolved.status.value == "RESOLVED"


@pytest.mark.asyncio
async def test_gtm_operations_deal_won_orchestration(async_session: AsyncSession):
    gtm_repo = SQLAlchemyGTMRepository(async_session)
    biz_repo = SQLAlchemyBusinessRepository(async_session)
    biz_service = BusinessOperationsService(biz_repo)

    gtm_service = GTMOperationsService(gtm_repo, business_service=biz_service)

    lead = await gtm_service.crm_service.create_lead("Apex Corp", "Alice Smith", "alice@apex.com")
    opp = await gtm_service.crm_service.create_opportunity("Apex Enterprise Deal", "prod-1", "sales-1", 5000000, lead_id=lead.id)

    result = await gtm_service.execute_deal_won_and_onboard(opp.id, actor_id="mgr-1", governance_approval_id="gov-app-won-1")
    assert result["status"] == "WON_AND_ONBOARDING_INITIATED"
    assert result["invoice_id"] is not None
    assert result["payment_id"] is not None
