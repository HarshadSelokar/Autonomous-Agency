"""
Unit tests for SQLAlchemy GTM Repository (Phase 24).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.gtm import (
    Product,
    ProductLifecycle,
    Customer,
    CustomerLifecycleState,
    Lead,
    LeadStatus,
    Opportunity,
    OpportunityStage,
    Proposal,
    ProposalStatus,
    SupportCase,
    SupportCaseStatus,
    MarketingCampaign,
    CampaignStatus,
)
from src.infrastructure.database import Base
import src.infrastructure.models.gtm_model
from src.infrastructure.repositories.gtm_repository import SQLAlchemyGTMRepository


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
async def test_product_and_customer_repository(async_session: AsyncSession):
    repo = SQLAlchemyGTMRepository(async_session)

    prod = Product(
        id="prod-100",
        name="AI Agent Operating System",
        code="PROD-AIOS",
        lifecycle=ProductLifecycle.ACTIVE,
        owner_employee_id="emp-1",
        base_price_cents=5000000,
    )
    await repo.save_product(prod)

    fetched_p = await repo.get_product_by_id("prod-100")
    assert fetched_p is not None
    assert fetched_p.name == "AI Agent Operating System"

    cust = Customer(
        id="cust-100",
        name="Global Tech Inc",
        domain="globaltech.com",
        lifecycle_state=CustomerLifecycleState.ACTIVE,
    )
    await repo.save_customer(cust)

    fetched_c = await repo.get_customer_by_id("cust-100")
    assert fetched_c is not None
    assert fetched_c.name == "Global Tech Inc"


@pytest.mark.asyncio
async def test_lead_opportunity_proposal_repository(async_session: AsyncSession):
    repo = SQLAlchemyGTMRepository(async_session)

    lead = Lead(
        id="lead-100",
        company_name="Apex Logistics",
        contact_name="John Doe",
        contact_email="john@apex.com",
        status=LeadStatus.QUALIFIED,
    )
    await repo.save_lead(lead)

    opp = Opportunity(
        id="opp-100",
        lead_id=lead.id,
        title="Apex AI Automation Deal",
        product_id="prod-100",
        stage=OpportunityStage.PROPOSAL,
        estimated_value_cents=10000000,
        owner_id="sales-rep-1",
    )
    await repo.save_opportunity(opp)

    prop = Proposal(
        id="prop-100",
        opportunity_id=opp.id,
        title="Apex Automation Proposal",
        product_id="prod-100",
        base_amount_cents=10000000,
        discount_pct=10.0,
        total_amount_cents=9000000,
        status=ProposalStatus.APPROVED,
        owner_id="sales-rep-1",
    )
    await repo.save_proposal(prop)

    fetched_prop = await repo.get_proposal_by_id("prop-100")
    assert fetched_prop is not None
    assert fetched_prop.total_amount_cents == 9000000
    assert fetched_prop.status == ProposalStatus.APPROVED
