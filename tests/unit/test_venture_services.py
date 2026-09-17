"""
Unit Tests for Phase 28 Venture Application Services & Safety Invariants.
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.venture_repository import SQLAlchemyVentureRepository
from src.application.innovation_discovery_service import InnovationDiscoveryService
from src.application.venture_business_case_service import VentureBusinessCaseService
from src.application.venture_proposal_service import VentureProposalService
from src.application.venture_lifecycle_service import VentureLifecycleService
from src.domain.venture import VentureType, ProposalStatus, LaunchReadinessStatus
from src.domain.exceptions import UnauthorizedVentureCreationError, VentureLaunchBlockedError


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
async def test_innovation_discovery_service_flow(session: AsyncSession):
    repo = SQLAlchemyVentureRepository(session)
    service = InnovationDiscoveryService(repo)
    company_id = "comp-svc-01"

    # Discover Opportunity
    opp = await service.discover_opportunity(
        company_id=company_id,
        title="Autonomous Logistics Optimization",
        description="Market demand for autonomous routing in supply chains.",
        problem_statement="High fuel costs and routing delays in fleet management.",
        customer_need="Real-time adaptive AI routing.",
    )
    assert opp.company_id == company_id

    # Generate Idea
    idea = await service.generate_idea(
        company_id=company_id,
        opportunity_id=opp.id,
        title="FleetPulse AI",
        description="Autonomous Fleet Dispatch Engine",
        proposed_solution="Dynamic reinforcement-learning route planner",
        target_customer="Enterprise Logistics Providers",
        value_proposition="25% reduction in fuel costs",
        differentiator="Sub-second real-time rerouting",
    )
    assert idea.opportunity_id == opp.id

    # Formulate Hypothesis
    hyp = await service.formulate_hypothesis(
        company_id=company_id,
        idea_id=idea.id,
        assumption="Logistics providers will pay $500/truck/month",
    )
    assert hyp.idea_id == idea.id

    # Validate Opportunity
    val = await service.validate_opportunity(
        company_id=company_id,
        opportunity_id=opp.id,
        validation_method="INTERVIEWS_AND_SIMULATION",
        evidence_summary="Verified against 30 logistics fleet managers.",
        confidence_score=0.88,
    )
    assert val.confidence_score == 0.88


@pytest.mark.asyncio
async def test_venture_proposal_governance_safety_invariant(session: AsyncSession):
    repo = SQLAlchemyVentureRepository(session)
    disc_svc = InnovationDiscoveryService(repo)
    case_svc = VentureBusinessCaseService(repo)
    prop_svc = VentureProposalService(repo)
    life_svc = VentureLifecycleService(repo)
    company_id = "comp-svc-01"

    opp = await disc_svc.discover_opportunity(
        company_id=company_id,
        title="AI Freight Matching Venture",
        description="Autonomous freight broker platform.",
        problem_statement="Unmatched empty backhaul truck trips.",
        customer_need="Automated spot rate freight matching.",
    )

    bcase = await case_svc.construct_business_case(
        company_id=company_id,
        opportunity_id=opp.id,
        title="Freight AI Business Case",
        expected_roi=0.40,
    )

    proposal = await prop_svc.propose_venture(
        company_id=company_id,
        opportunity_id=opp.id,
        business_case_id=bcase.id,
        title="Freight AI Venture",
        venture_type=VentureType.NEW_COMPANY,
        governance_required=True,
    )

    # Attempt initialization WITHOUT governance approval -> MUST FAIL
    with pytest.raises(UnauthorizedVentureCreationError):
        await life_svc.initialize_venture(
            proposal_id=proposal.id,
            company_id=company_id,
            target_structure=VentureType.NEW_COMPANY,
        )

    # Attach governance approval
    await prop_svc.attach_governance_approval(
        proposal_id=proposal.id,
        company_id=company_id,
        governance_approval_id="gov-appr-passed-101",
    )

    # Initialize WITH governance approval -> MUST SUCCEED
    init_res = await life_svc.initialize_venture(
        proposal_id=proposal.id,
        company_id=company_id,
        target_structure=VentureType.NEW_COMPANY,
    )
    assert init_res["governance_approval_id"] == "gov-appr-passed-101"


@pytest.mark.asyncio
async def test_venture_launch_readiness_and_outcome_service(session: AsyncSession):
    repo = SQLAlchemyVentureRepository(session)
    disc_svc = InnovationDiscoveryService(repo)
    case_svc = VentureBusinessCaseService(repo)
    prop_svc = VentureProposalService(repo)
    life_svc = VentureLifecycleService(repo)
    company_id = "comp-svc-01"

    opp = await disc_svc.discover_opportunity(
        company_id=company_id,
        title="AI Document OCR Venture",
        description="High throughput document OCR.",
        problem_statement="Manual data entry bottlenecks.",
        customer_need="Automated OCR parsing.",
    )

    bcase = await case_svc.construct_business_case(
        company_id=company_id,
        opportunity_id=opp.id,
        title="OCR Business Case",
    )

    proposal = await prop_svc.propose_venture(
        company_id=company_id,
        opportunity_id=opp.id,
        business_case_id=bcase.id,
        title="OCR Venture",
    )

    await prop_svc.attach_governance_approval(
        proposal_id=proposal.id,
        company_id=company_id,
        governance_approval_id="gov-appr-ocr-202",
    )

    # Launch without assessing readiness -> MUST FAIL
    with pytest.raises(VentureLaunchBlockedError):
        await life_svc.launch_venture(proposal_id=proposal.id, company_id=company_id)

    # Assess readiness with all flags True
    readiness = await life_svc.assess_launch_readiness(
        proposal_id=proposal.id,
        company_id=company_id,
        product_ready=True,
        technical_ready=True,
        security_ready=True,
        financial_ready=True,
        governance_ready=True,
    )
    assert readiness.status == LaunchReadinessStatus.READY

    # Launch venture -> MUST SUCCEED
    launch_res = await life_svc.launch_venture(proposal_id=proposal.id, company_id=company_id)
    assert launch_res["status"] == "LAUNCHED"

    # Evaluate outcome
    outcome = await life_svc.evaluate_venture_outcome(
        venture_id=proposal.id,
        company_id=company_id,
        expected_outcomes={"arr_usd": 500000},
        actual_outcomes={"arr_usd": 540000},
    )
    assert outcome.status.value == "SUCCEEDED"
