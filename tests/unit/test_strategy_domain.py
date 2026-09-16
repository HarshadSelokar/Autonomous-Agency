"""
Unit tests for Strategy domain entities.
"""

import pytest

from src.domain.strategy import (
    CompanyStrategy,
    StrategyProposal,
    StrategyProposalStatus,
    StrategyProposalType,
    StrategySimulation,
    StrategyStatus,
)


def test_company_strategy_versioning():
    strat_v1 = CompanyStrategy(
        company_id="comp-1",
        version=1,
        title="Q1 Expansion Strategy",
        themes=["AI Automation", "Security Rigor"],
        status=StrategyStatus.ACTIVE,
    )
    assert strat_v1.version == 1
    assert strat_v1.status == StrategyStatus.ACTIVE

    strat_v2 = CompanyStrategy(
        company_id="comp-1",
        version=2,
        title="Q2 Scaling Strategy",
        previous_version_id=strat_v1.id,
        change_rationale="Evolving market demand",
    )
    assert strat_v2.version == 2
    assert strat_v2.previous_version_id == strat_v1.id


def test_strategic_proposal_creation():
    proposal = StrategyProposal(
        company_id="comp-1",
        proposal_type=StrategyProposalType.WORKFORCE_REQUEST,
        title="Expand QA Capability",
        proposal="Hire 2 additional QA engineers",
        reason="QA capacity bottleneck detected",
        reversibility="HIGH",
        governance_level="HUMAN_GOVERNANCE_REQUIRED",
    )
    assert proposal.status == StrategyProposalStatus.PROPOSED
    assert proposal.governance_level == "HUMAN_GOVERNANCE_REQUIRED"


def test_strategy_simulation_isolation_invariant():
    """
    INVARIANT TEST:
    A StrategySimulation can NEVER be initialized with is_authoritative = True.
    """
    with pytest.raises(ValueError, match="Simulation state cannot be declared authoritative"):
        StrategySimulation(
            company_id="comp-1",
            title="Aggressive Hiring What-If",
            is_authoritative=True,
        )

    sim = StrategySimulation(
        company_id="comp-1",
        title="Valid Simulation Scenario",
        is_authoritative=False,
    )
    assert sim.is_authoritative is False
