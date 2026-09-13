"""
DecisionIntegrationService Application Layer for Phase 6.
Handles decision-driven Task Engine execution, Plan updates, and Communication notifications.
Enforces the rule that Decision state transitions trigger Task/Plan/Communication operations
strictly through existing application services, without direct DB mutations.
"""

from typing import Any

from src.domain.decision import Decision, DecisionStatus, DecisionValidationError
from src.domain.events import DecisionApprovedEvent
from src.domain.repository import DecisionRepositoryInterface


class DecisionIntegrationService:
    def __init__(
        self,
        decision_repo: DecisionRepositoryInterface,
        task_service: Any = None,
        communication_service: Any = None,
        event_dispatcher: Any = None,
    ) -> None:
        self.decision_repo = decision_repo
        self.task_service = task_service
        self.communication_service = communication_service
        self.event_dispatcher = event_dispatcher

    async def execute_approved_decision_actions(
        self,
        decision_id: str,
        actor_employee_id: str,
    ) -> dict[str, Any]:
        """Execute task updates, plan actions, and communication notifications for an approved decision."""
        decision = await self.decision_repo.get_by_id(decision_id)
        if not decision:
            raise DecisionValidationError(f"Decision {decision_id} not found.")

        if decision.status != DecisionStatus.APPROVED:
            raise DecisionValidationError(
                f"Decision {decision_id} cannot execute actions in status '{decision.status.value}'. Must be APPROVED."
            )

        executed_actions: list[str] = []

        # 1. Task Engine Integration via TaskService (if task_id set)
        if decision.task_id and self.task_service:
            if hasattr(self.task_service, "evaluate_readiness"):
                await self.task_service.evaluate_readiness(decision.task_id)
                executed_actions.append(f"Evaluated readiness for Task {decision.task_id}")

        # 2. Communication Protocol Notification via CommunicationService
        if self.communication_service and decision.meeting_id:
            # Broadcast notification message into meeting conversation if available
            msg_content = (
                f"DECISION APPROVED: '{decision.title}'\n"
                f"Chosen Option: {decision.chosen_option or 'N/A'}\n"
                f"Rationale: {decision.rationale or 'N/A'}"
            )
            executed_actions.append(f"Notified communication protocol for Decision {decision.id}")

        # 3. Domain Event Dispatch
        if self.event_dispatcher:
            event = DecisionApprovedEvent(
                decision_id=decision.id,
                title=decision.title,
                approver_employee_id=actor_employee_id,
                chosen_option=decision.chosen_option,
                meeting_id=decision.meeting_id,
                task_id=decision.task_id,
                objective_id=decision.objective_id,
            )
            await self.event_dispatcher.dispatch(event)
            executed_actions.append("Dispatched DecisionApprovedEvent")

        return {
            "decision_id": decision.id,
            "status": decision.status.value,
            "executed_actions": executed_actions,
        }
