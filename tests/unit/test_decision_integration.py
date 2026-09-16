"""
Unit tests for DecisionIntegrationService (Task, Plan, and Communication actions).
"""

from typing import Any

import pytest

from src.application.decision_integration_service import DecisionIntegrationService
from src.domain.decision import Decision, DecisionStatus, DecisionValidationError


class MemoryDecisionRepository:
    def __init__(self) -> None:
        self.decisions: dict[str, Decision] = {}

    async def save(self, decision: Decision) -> Decision:
        self.decisions[decision.id] = decision
        return decision

    async def get_by_id(self, decision_id: str) -> Decision | None:
        return self.decisions.get(decision_id)


class MockTaskService:
    def __init__(self) -> None:
        self.evaluated_task_ids: list[str] = []

    async def evaluate_readiness(self, task_id: str) -> None:
        self.evaluated_task_ids.append(task_id)


class MockEventDispatcher:
    def __init__(self) -> None:
        self.dispatched_events: list[Any] = []

    async def dispatch(self, event: Any) -> None:
        self.dispatched_events.append(event)


@pytest.mark.asyncio
async def test_execute_approved_decision_actions_success() -> None:
    repo = MemoryDecisionRepository()
    task_service = MockTaskService()
    dispatcher = MockEventDispatcher()

    decision = Decision(
        id="d-exec-1",
        title="Approve PostgreSQL",
        question="Use PostgreSQL database?",
        decision_maker_employee_id="emp-mgr",
        status=DecisionStatus.APPROVED,
        task_id="t-100",
        chosen_option="PostgreSQL",
    )
    await repo.save(decision)

    service = DecisionIntegrationService(
        decision_repo=repo,
        task_service=task_service,
        event_dispatcher=dispatcher,
    )

    result = await service.execute_approved_decision_actions("d-exec-1", actor_employee_id="emp-mgr")
    assert result["decision_id"] == "d-exec-1"
    assert "t-100" in task_service.evaluated_task_ids
    assert len(dispatcher.dispatched_events) == 1
    assert dispatcher.dispatched_events[0].decision_id == "d-exec-1"


@pytest.mark.asyncio
async def test_execute_unapproved_decision_actions_fails() -> None:
    repo = MemoryDecisionRepository()
    decision = Decision(
        id="d-exec-2",
        title="Proposed Architecture",
        question="Question",
        decision_maker_employee_id="emp-dev",
        status=DecisionStatus.PROPOSED,
    )
    await repo.save(decision)

    service = DecisionIntegrationService(decision_repo=repo)
    with pytest.raises(DecisionValidationError, match="Must be APPROVED"):
        await service.execute_approved_decision_actions("d-exec-2", actor_employee_id="emp-dev")
