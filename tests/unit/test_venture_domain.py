"""
Unit Tests for Phase 28 Venture & Innovation Domain Models & Safety Invariants.
"""

import pytest
from src.domain.venture import (
    InnovationOpportunity,
    OpportunityStatus,
    VentureProposal,
    ProposalStatus,
    VentureType,
    VentureLaunchReadiness,
    LaunchReadinessStatus,
)
from src.domain.exceptions import (
    UnauthorizedVentureCreationError,
    InvalidVentureLifecycleError,
)


def test_opportunity_creation_defaults():
    opp = InnovationOpportunity(
        company_id="comp-test-01",
        title="AI Automated Invoice Processing Venture",
        description="Market opportunity for automated enterprise invoice reconciliation.",
    )
    assert opp.company_id == "comp-test-01"
    assert opp.status == OpportunityStatus.DISCOVERED
    assert opp.confidence == 0.50


def test_governance_safety_boundary_enforcement():
    proposal = VentureProposal(
        company_id="comp-test-01",
        title="Invoice Automation Venture Proposal",
        venture_type=VentureType.NEW_COMPANY,
        governance_required=True,
        governance_approval_id=None,
    )

    # Must fail without governance approval ID
    with pytest.raises(UnauthorizedVentureCreationError):
        proposal.assert_valid_for_initialization()

    # Set governance approval ID -> Must pass
    proposal.governance_approval_id = "gov-appr-test-123"
    proposal.assert_valid_for_initialization()


def test_proposal_lifecycle_status_transitions():
    proposal = VentureProposal(
        company_id="comp-test-01",
        title="Invoice Automation Venture Proposal",
        status=ProposalStatus.PROPOSED,
    )

    # Valid transition: PROPOSED -> UNDER_REVIEW
    proposal.transition_status(ProposalStatus.UNDER_REVIEW)
    assert proposal.status == ProposalStatus.UNDER_REVIEW

    # Valid transition: UNDER_REVIEW -> GOVERNANCE_PENDING
    proposal.transition_status(ProposalStatus.GOVERNANCE_PENDING)
    assert proposal.status == ProposalStatus.GOVERNANCE_PENDING

    # Valid transition: GOVERNANCE_PENDING -> APPROVED
    proposal.transition_status(ProposalStatus.APPROVED)
    assert proposal.status == ProposalStatus.APPROVED

    # Invalid transition: APPROVED -> REJECTED (Must fail)
    with pytest.raises(InvalidVentureLifecycleError):
        proposal.transition_status(ProposalStatus.REJECTED)


def test_venture_launch_readiness_evaluation():
    readiness = VentureLaunchReadiness(
        company_id="comp-test-01",
        product_ready=True,
        technical_ready=True,
        security_ready=True,
        financial_ready=False,  # Financial readiness missing!
        governance_ready=True,
    )

    status = readiness.evaluate_readiness()
    assert status == LaunchReadinessStatus.BLOCKED

    readiness.financial_ready = True
    status = readiness.evaluate_readiness()
    assert status == LaunchReadinessStatus.READY
