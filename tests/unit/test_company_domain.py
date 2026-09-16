"""
Unit tests for Autonomous Company domain entities.
"""

import pytest
from src.domain.company import (
    AutonomousCompany,
    CompanyHealthSnapshot,
    CompanyHealthStatus,
    CompanyKPISnapshot,
    CompanyOperatingCycle,
    CompanyOpportunity,
    CompanyRisk,
    CompanyStatus,
    MetricTrend,
    OperatingCycleState,
    PortfolioItem,
    RiskSeverity,
)


def test_autonomous_company_creation():
    company = AutonomousCompany(name="Global Autonomous Corp", code="GAC")
    assert company.name == "Global Autonomous Corp"
    assert company.code == "GAC"
    assert company.status == CompanyStatus.ACTIVE


def test_operating_cycle_lifecycle():
    cycle = CompanyOperatingCycle(company_id="comp-1", cycle_number=1)
    assert cycle.state == OperatingCycleState.CREATED

    cycle.transition_to(OperatingCycleState.OBSERVING)
    assert cycle.state == OperatingCycleState.OBSERVING

    cycle.transition_to(OperatingCycleState.ANALYZING)
    assert cycle.state == OperatingCycleState.ANALYZING

    cycle.transition_to(OperatingCycleState.PLANNING)
    assert cycle.state == OperatingCycleState.PLANNING

    cycle.transition_to(OperatingCycleState.PRIORITIZING)
    assert cycle.state == OperatingCycleState.PRIORITIZING

    cycle.transition_to(OperatingCycleState.AWAITING_GOVERNANCE)
    assert cycle.state == OperatingCycleState.AWAITING_GOVERNANCE

    cycle.transition_to(OperatingCycleState.EXECUTING)
    assert cycle.state == OperatingCycleState.EXECUTING

    cycle.transition_to(OperatingCycleState.MEASURING)
    assert cycle.state == OperatingCycleState.MEASURING

    cycle.transition_to(OperatingCycleState.LEARNING)
    assert cycle.state == OperatingCycleState.LEARNING

    cycle.transition_to(OperatingCycleState.COMPLETED)
    assert cycle.state == OperatingCycleState.COMPLETED
    assert cycle.completed_at is not None


def test_invalid_operating_cycle_transition():
    cycle = CompanyOperatingCycle(company_id="comp-1")
    with pytest.raises(ValueError, match="Invalid operating cycle state transition"):
        cycle.transition_to(OperatingCycleState.EXECUTING)


def test_company_kpi_snapshot():
    kpi = CompanyKPISnapshot(
        company_id="comp-1",
        metric_name="task_success_rate",
        value=0.98,
        target_value=0.95,
        trend=MetricTrend.UP,
    )
    assert kpi.value == 0.98
    assert kpi.trend == MetricTrend.UP


def test_company_risk_and_opportunity():
    risk = CompanyRisk(
        company_id="comp-1",
        title="Capacity Constraint",
        severity=RiskSeverity.HIGH,
        probability=0.7,
        impact=0.8,
    )
    assert risk.severity == RiskSeverity.HIGH

    opp = CompanyOpportunity(
        company_id="comp-1",
        title="Automated Test Expansion",
        expected_value=50000.0,
    )
    assert opp.expected_value == 50000.0
