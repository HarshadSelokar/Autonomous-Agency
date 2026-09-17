"""
Unit tests for PlatformControlPlane, CompanyReadinessCheck, EnterpriseReadinessCheck, & PlatformWorkflowEngine (Phase 31).
"""

import pytest

from src.application.platform_control_plane import CompanyLifecycleState, PlatformControlPlane
from src.application.workflows.platform_workflows import PlatformWorkflowEngine, WorkflowCategory, WorkflowState


def test_platform_control_plane_company_readiness():
    control_plane = PlatformControlPlane()

    # 1. Evaluate readiness with all parameters healthy
    result = control_plane.evaluate_company_readiness("comp-test-01")
    assert result.is_ready is True
    assert result.readiness_score == 100.0
    assert len(result.checklist) == 9

    # 2. Transition company state to ACTIVE
    new_state = control_plane.transition_company_state("comp-test-01", CompanyLifecycleState.ACTIVE, readiness_result=result)
    assert new_state == CompanyLifecycleState.ACTIVE
    assert control_plane.get_company_state("comp-test-01") == CompanyLifecycleState.ACTIVE


def test_platform_control_plane_failed_readiness_blocks_activation():
    control_plane = PlatformControlPlane()

    # Readiness fails if database is unhealthy and has no governance policy
    failed_result = control_plane.evaluate_company_readiness("comp-failed", db_healthy=False, has_governance_policy=False)
    assert failed_result.is_ready is False
    assert failed_result.readiness_score < 90.0

    # Attempting to activate company with failed readiness raises ValueError
    with pytest.raises(ValueError) as exc_info:
        control_plane.transition_company_state("comp-failed", CompanyLifecycleState.ACTIVE, readiness_result=failed_result)

    assert "Readiness check failed" in str(exc_info.value)


def test_platform_workflow_engine_lifecycle():
    engine = PlatformWorkflowEngine()

    # 1. Start workflow
    record = engine.start_workflow(
        name="Objective Execution Workflow",
        category=WorkflowCategory.OBJECTIVE_TO_EXECUTION,
        company_id="comp-main-01",
    )
    assert record.state == WorkflowState.RUNNING
    assert record.current_step == "1_VALIDATING_INPUTS"

    # 2. Advance step
    advanced = engine.advance_step(record.workflow_id, next_step="2_DECOMPOSING_TASKS", step_data={"tasks_created": 3})
    assert advanced.current_step == "2_DECOMPOSING_TASKS"
    assert "1_VALIDATING_INPUTS" in advanced.completed_steps

    # 3. Transition to COMPLETED
    completed = engine.transition_state(record.workflow_id, WorkflowState.COMPLETED)
    assert completed.state == WorkflowState.COMPLETED
    assert completed.completed_at is not None
