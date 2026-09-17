"""
Unit Tests for Phase 27 Continuous Organizational Learning & Governed Adaptation Domain Models.
"""

import pytest
from src.domain.learning import (
    LearningCycle,
    LearningCycleStatus,
    LearningObservation,
    ExpectedVsActualComparison,
    LearningCandidate,
    LearningValidation,
    LearningPattern,
    ImprovementOpportunity,
    AdaptationProposal,
    AdaptationStatus,
    AdaptationType,
    AdaptationRiskLevel,
)
from src.domain.exceptions import (
    InvalidLearningCycleStateError,
    InvalidAdaptationStateError,
    UnauthorizedAdaptationExecutionError,
)


def test_learning_cycle_status_transitions():
    cycle = LearningCycle(company_id="comp-test-01", purpose="Test Learning Cycle")
    assert cycle.status == LearningCycleStatus.CREATED

    # Transition to COLLECTING
    cycle.transition_status(LearningCycleStatus.COLLECTING)
    assert cycle.status == LearningCycleStatus.COLLECTING

    # Transition to ANALYZING
    cycle.transition_status(LearningCycleStatus.ANALYZING)
    assert cycle.status == LearningCycleStatus.ANALYZING

    # Invalid transition directly to COMPLETED
    with pytest.raises(InvalidLearningCycleStateError):
        cycle.transition_status(LearningCycleStatus.COMPLETED)


def test_adaptation_proposal_governance_boundary():
    proposal = AdaptationProposal(
        company_id="comp-test-01",
        opportunity_id="opp-101",
        adaptation_type=AdaptationType.WORKFLOW_CHANGE,
        risk_level=AdaptationRiskLevel.HIGH,
        governance_required=True,
        governance_approval_id=None,
    )

    # Execution without governance approval ID -> MUST FAIL!
    with pytest.raises(UnauthorizedAdaptationExecutionError):
        proposal.assert_valid_for_execution()

    # With governance approval ID -> MUST SUCCEED!
    proposal.governance_approval_id = "gov-appr-test-123"
    proposal.assert_valid_for_execution()  # No exception raised


def test_adaptation_proposal_status_transitions():
    proposal = AdaptationProposal(company_id="comp-test-01", opportunity_id="opp-101")
    assert proposal.status == AdaptationStatus.PROPOSED

    proposal.transition_status(AdaptationStatus.ANALYZING)
    assert proposal.status == AdaptationStatus.ANALYZING

    proposal.transition_status(AdaptationStatus.APPROVED)
    assert proposal.status == AdaptationStatus.APPROVED

    with pytest.raises(InvalidAdaptationStateError):
        proposal.transition_status(AdaptationStatus.ROLLED_BACK)
