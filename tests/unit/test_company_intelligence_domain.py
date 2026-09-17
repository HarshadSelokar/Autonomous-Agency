"""
Unit tests for Phase 26 Company Intelligence & Decision Support Domain Models.
"""

import pytest
from datetime import UTC, datetime

from src.domain.company_intelligence import (
    IntelligenceRun,
    IntelligenceRunStatus,
    DecisionQuestion,
    DecisionOption,
    DecisionEvaluation,
    DecisionInsight,
    CompanyHealthAssessment,
    CompanyBottleneck,
    CompanyRiskAssessment,
    CompanyOpportunityAssessment,
    DecisionOutcomeEvaluation,
    QuestionUrgency,
    RiskCategory,
)
from src.domain.exceptions import (
    InvalidIntelligenceRunStateError,
    DecisionInsightExpiredError,
    UnauthorizedDecisionExecutionError,
)


def test_intelligence_run_state_transitions():
    run = IntelligenceRun(company_id="comp-01", purpose="Strategic evaluation")
    assert run.status == IntelligenceRunStatus.REQUESTED

    # Valid transitions: REQUESTED -> COLLECTING_DATA -> ANALYZING -> MODELING -> EVALUATING -> GENERATING_INSIGHTS -> COMPLETED
    run.transition_status(IntelligenceRunStatus.COLLECTING_DATA)
    assert run.status == IntelligenceRunStatus.COLLECTING_DATA

    run.transition_status(IntelligenceRunStatus.ANALYZING)
    run.transition_status(IntelligenceRunStatus.MODELING)
    run.transition_status(IntelligenceRunStatus.EVALUATING)
    run.transition_status(IntelligenceRunStatus.GENERATING_INSIGHTS)
    run.transition_status(IntelligenceRunStatus.COMPLETED)
    assert run.status == IntelligenceRunStatus.COMPLETED

    # Terminal state transition fails
    with pytest.raises(InvalidIntelligenceRunStateError):
        run.transition_status(IntelligenceRunStatus.ANALYZING)


def test_decision_insight_execution_governance_validation():
    insight = DecisionInsight(
        question_id="q-101",
        company_id="comp-01",
        recommendation_summary="Expand engineering team",
        governance_required=True,
        governance_approval_id=None,  # Unapproved
    )

    # Execution without governance approval raises UnauthorizedDecisionExecutionError
    with pytest.raises(UnauthorizedDecisionExecutionError):
        insight.assert_valid_for_execution()

    # Approve insight
    insight.governance_approval_id = "gov-appr-999"
    insight.assert_valid_for_execution()  # Passes

    # Expired insight raises DecisionInsightExpiredError
    insight.is_expired = True
    with pytest.raises(DecisionInsightExpiredError):
        insight.assert_valid_for_execution()


def test_decision_option_no_action_baseline():
    opt_no_action = DecisionOption(
        question_id="q-101",
        company_id="comp-01",
        option_name="Option 0: Maintain Current Capacity",
        is_no_action_baseline=True,
    )
    assert opt_no_action.is_no_action_baseline is True

    opt_expand = DecisionOption(
        question_id="q-101",
        company_id="comp-01",
        option_name="Option 1: Add 5 Engineers",
        is_no_action_baseline=False,
        expected_costs_cents=5000000,
    )
    assert opt_expand.is_no_action_baseline is False
    assert opt_expand.expected_costs_cents == 5000000
