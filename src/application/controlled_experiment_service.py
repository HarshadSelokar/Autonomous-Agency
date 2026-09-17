"""
Controlled Experiment & Governed Execution Application Service for Phase 27.

Manages experiment dispatches, control vs treatment evaluations, regression monitoring,
and adaptation rollback execution.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.learning import (
    AdaptationProposal,
    AdaptationStatus,
    AdaptationExecution,
    AdaptationOutcome,
)
from src.domain.exceptions import (
    UnauthorizedAdaptationExecutionError,
    AdaptationRollbackError,
)
from src.domain.events import (
    AdaptationExperimentDispatchedEvent,
    AdaptationAdoptedEvent,
    AdaptationRolledBackEvent,
    AdaptationOutcomeRecordedEvent,
)
from src.domain.repository import LearningRepositoryInterface


class ControlledExperimentService:
    """Dispatches bounded controlled experiments, evaluates outcome metrics, and executes rollbacks."""

    def __init__(self, repository: LearningRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def dispatch_experiment(
        self,
        proposal_id: str,
        company_id: str,
        actor_id: str,
        governance_approval_id: str,
        target_subsystem: str = "WORKFLOW_ENGINE",
    ) -> AdaptationExecution:
        proposal = await self.repository.get_adaptation_proposal_by_id(proposal_id)
        if not proposal or proposal.company_id != company_id:
            raise ValueError(f"Adaptation proposal '{proposal_id}' not found.")

        # Attach governance approval ID if provided
        if governance_approval_id:
            proposal.governance_approval_id = governance_approval_id

        # Enforce fundamental invariant: proposal cannot execute without governance approval
        proposal.assert_valid_for_execution()

        proposal.transition_status(AdaptationStatus.EXPERIMENTING)
        await self.repository.save_adaptation_proposal(proposal)

        execution = AdaptationExecution(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            company_id=company_id,
            governance_approval_id=governance_approval_id,
            execution_type="CONTROLLED_EXPERIMENT",
            target_subsystem=target_subsystem,
            execution_payload={
                "actor_id": actor_id,
                "proposed_state": proposal.proposed_state,
                "current_state": proposal.current_state,
            },
            dispatched_at=datetime.now(UTC),
        )
        saved = await self.repository.save_adaptation_execution(execution)

        self._publish_event(
            AdaptationExperimentDispatchedEvent(
                execution_id=saved.id,
                proposal_id=proposal_id,
                company_id=company_id,
                governance_approval_id=governance_approval_id,
            )
        )
        return saved

    async def evaluate_experiment_outcome(
        self,
        execution_id: str,
        company_id: str,
        expected_metrics: Dict[str, Any],
        actual_metrics: Dict[str, Any],
        side_effects_detected: Optional[List[str]] = None,
    ) -> AdaptationOutcome:
        execution = await self.repository.get_adaptation_execution_by_id(execution_id)
        if not execution or execution.company_id != company_id:
            raise ValueError(f"Adaptation execution '{execution_id}' not found.")

        proposal = await self.repository.get_adaptation_proposal_by_id(execution.proposal_id)

        # Detect regression
        has_regression = False
        for k, exp_v in expected_metrics.items():
            act_v = actual_metrics.get(k)
            if isinstance(exp_v, (int, float)) and isinstance(act_v, (int, float)):
                if act_v < exp_v * 0.85:  # >15% drop under expected threshold
                    has_regression = True
                    break

        variance_analysis = {
            "expected": expected_metrics,
            "actual": actual_metrics,
            "status": "REGRESSION" if has_regression else "SUCCESS",
        }

        outcome = AdaptationOutcome(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            proposal_id=execution.proposal_id,
            company_id=company_id,
            expected_metrics=expected_metrics,
            actual_metrics=actual_metrics,
            variance_analysis=variance_analysis,
            side_effects_detected=side_effects_detected or [],
            has_regression=has_regression,
            measured_at=datetime.now(UTC),
        )
        saved = await self.repository.save_adaptation_outcome(outcome)

        execution.completed_at = datetime.now(UTC)
        await self.repository.save_adaptation_execution(execution)

        if proposal:
            if proposal.status == AdaptationStatus.EXPERIMENTING:
                proposal.transition_status(AdaptationStatus.EVALUATING)
                await self.repository.save_adaptation_proposal(proposal)

        self._publish_event(
            AdaptationOutcomeRecordedEvent(
                outcome_id=saved.id,
                proposal_id=execution.proposal_id,
                company_id=company_id,
                has_regression=has_regression,
            )
        )
        return saved

    async def adopt_adaptation(self, proposal_id: str, company_id: str) -> AdaptationProposal:
        proposal = await self.repository.get_adaptation_proposal_by_id(proposal_id)
        if not proposal or proposal.company_id != company_id:
            raise ValueError(f"Adaptation proposal '{proposal_id}' not found.")

        proposal.transition_status(AdaptationStatus.ADOPTED)
        saved = await self.repository.save_adaptation_proposal(proposal)

        self._publish_event(
            AdaptationAdoptedEvent(proposal_id=proposal_id, company_id=company_id)
        )
        return saved

    async def rollback_adaptation(
        self, proposal_id: str, company_id: str, reason: str = "Regression detected during outcome evaluation."
    ) -> AdaptationProposal:
        proposal = await self.repository.get_adaptation_proposal_by_id(proposal_id)
        if not proposal or proposal.company_id != company_id:
            raise ValueError(f"Adaptation proposal '{proposal_id}' not found.")

        if not proposal.rollback_plan:
            raise AdaptationRollbackError(proposal_id, "No valid rollback plan defined for proposal.")

        proposal.transition_status(AdaptationStatus.ROLLED_BACK)
        saved = await self.repository.save_adaptation_proposal(proposal)

        self._publish_event(
            AdaptationRolledBackEvent(proposal_id=proposal_id, company_id=company_id, reason=reason)
        )
        return saved
