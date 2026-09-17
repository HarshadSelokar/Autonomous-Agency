"""
Unit Tests for SQLAlchemyVentureRepository (Phase 28).
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.venture_repository import SQLAlchemyVentureRepository
from src.domain.venture import (
    InnovationOpportunity,
    OpportunityStatus,
    VentureBusinessCase,
    BusinessCaseStatus,
    VentureProposal,
    VentureType,
    ProposalStatus,
)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as sess:
        yield sess

    await engine.dispose()


@pytest.mark.asyncio
async def test_venture_repository_save_and_retrieve(session: AsyncSession):
    repo = SQLAlchemyVentureRepository(session)
    company_id = "comp-repo-test-01"

    # Save Opportunity
    opp = InnovationOpportunity(
        company_id=company_id,
        title="AI Medical Diagnostics Opportunity",
        description="Autonomous medical imaging diagnostics SaaS opportunity.",
        potential_impact="HIGH_GROWTH",
    )
    saved_opp = await repo.save_opportunity(opp)
    assert saved_opp.id == opp.id

    fetched_opp = await repo.get_opportunity_by_id(opp.id)
    assert fetched_opp is not None
    assert fetched_opp.title == "AI Medical Diagnostics Opportunity"

    # Save Business Case
    bcase = VentureBusinessCase(
        opportunity_id=opp.id,
        company_id=company_id,
        title="AI Medical Diagnostics Business Case",
        expected_roi=0.45,
        status=BusinessCaseStatus.DRAFT,
    )
    saved_bcase = await repo.save_business_case(bcase)
    assert saved_bcase.id == bcase.id

    # Save Proposal
    proposal = VentureProposal(
        opportunity_id=opp.id,
        company_id=company_id,
        title="Medical AI Venture Proposal",
        venture_type=VentureType.NEW_COMPANY,
        business_case_id=bcase.id,
        status=ProposalStatus.PROPOSED,
    )
    saved_prop = await repo.save_proposal(proposal)
    assert saved_prop.id == proposal.id

    # List proposals for company
    props = await repo.list_proposals_for_company(company_id)
    assert len(props) == 1
    assert props[0].title == "Medical AI Venture Proposal"
