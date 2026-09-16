"""
Unit tests for Phase 25 Multi-Company & Simulation domain models.
"""

import pytest
from src.domain.company import (
    Company,
    CompanyLifecycle,
    CompanyContext,
    CompanyRole,
    ExecutionEnvironment,
)
from src.domain.simulation import (
    CompanySimulation,
    SimulationStatus,
)
from src.domain.exceptions import (
    InvalidLifecycleTransitionError,
    TenantIsolationViolationError,
    SimulationProductionMutationError,
)


def test_company_lifecycle_valid_transitions():
    company = Company(name="Acme Autonomous Corp", slug="acme-corp")
    assert company.lifecycle == CompanyLifecycle.PROPOSED

    # PROPOSED -> INITIALIZING -> ACTIVE -> PAUSED -> ACTIVE -> SUSPENDED -> ACTIVE -> ARCHIVED
    company.transition_lifecycle(CompanyLifecycle.INITIALIZING)
    assert company.lifecycle == CompanyLifecycle.INITIALIZING

    company.transition_lifecycle(CompanyLifecycle.ACTIVE)
    assert company.lifecycle == CompanyLifecycle.ACTIVE

    company.transition_lifecycle(CompanyLifecycle.PAUSED)
    assert company.lifecycle == CompanyLifecycle.PAUSED

    company.transition_lifecycle(CompanyLifecycle.ACTIVE)
    assert company.lifecycle == CompanyLifecycle.ACTIVE

    company.transition_lifecycle(CompanyLifecycle.SUSPENDED)
    assert company.lifecycle == CompanyLifecycle.SUSPENDED

    company.transition_lifecycle(CompanyLifecycle.ACTIVE)
    assert company.lifecycle == CompanyLifecycle.ACTIVE

    company.transition_lifecycle(CompanyLifecycle.ARCHIVED)
    assert company.lifecycle == CompanyLifecycle.ARCHIVED


def test_company_lifecycle_invalid_transition():
    company = Company(name="Acme Corp", slug="acme")
    # Cannot jump directly from PROPOSED to ACTIVE or PAUSED
    with pytest.raises(InvalidLifecycleTransitionError):
        company.transition_lifecycle(CompanyLifecycle.ACTIVE)

    company.transition_lifecycle(CompanyLifecycle.INITIALIZING)
    company.transition_lifecycle(CompanyLifecycle.ACTIVE)
    company.transition_lifecycle(CompanyLifecycle.ARCHIVED)

    # ARCHIVED is terminal, cannot transition out
    with pytest.raises(InvalidLifecycleTransitionError):
        company.transition_lifecycle(CompanyLifecycle.ACTIVE)


def test_company_context_tenant_isolation():
    ctx_company_a = CompanyContext(company_id="comp-A", user_id="user-1", role=CompanyRole.ADMIN)

    # Same company access -> succeeds
    ctx_company_a.verify_company_access("comp-A", "workspace")

    # Cross company access -> raises TenantIsolationViolationError
    with pytest.raises(TenantIsolationViolationError) as exc_info:
        ctx_company_a.verify_company_access("comp-B", "task")

    assert "comp-A" in str(exc_info.value)
    assert "comp-B" in str(exc_info.value)


def test_simulation_safety_assertion():
    sim = CompanySimulation(
        company_id="comp-A",
        name="Q4 Staffing Growth Simulation",
        environment=ExecutionEnvironment.SIMULATION,
        status=SimulationStatus.RUNNING,
    )

    # Safe simulation query -> succeeds
    sim.assert_simulation_safety("QUERY_SIMULATED_REVENUE")

    # Blocked production mutating action -> raises SimulationProductionMutationError
    with pytest.raises(SimulationProductionMutationError) as exc_info:
        sim.assert_simulation_safety("CHARGE_CREDIT_CARD")

    assert "CHARGE_CREDIT_CARD" in str(exc_info.value)
