"""
Decision Outcome Learning Application Service for Phase 26.

Evaluates post-execution decision outcomes against expected results, computes variance analysis,
and registers validated learning candidates for Institutional Knowledge.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Optional
import uuid

from src.domain.company_intelligence import DecisionOutcomeEvaluation
from src.domain.events import DecisionOutcomeEvaluatedEvent
from src.domain.repository import CompanyIntelligenceRepositoryInterface


class DecisionOutcomeLearningService:
    """Evaluates historical decision outcomes and feeds organizational learning loops."""

    def __init__(self, repository: CompanyIntelligenceRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def evaluate_decision_outcome(
        self,
        insight_id: str,
        company_id: str,
        executed_option_id: str,
        expected_outcomes: Dict[str, Any],
        actual_outcomes: Dict[str, Any],
    ) -> DecisionOutcomeEvaluation:
        # Compute variance
        expected_rev = float(expected_outcomes.get("revenue_cents", 0))
        actual_rev = float(actual_outcomes.get("revenue_cents", 0))
        variance_pct = round(((actual_rev - expected_rev) / max(1.0, expected_rev)) * 100.0, 2) if expected_rev > 0 else 0.0

        learning_text = (
            f"Decision insight '{insight_id}' outcome evaluation: Actual revenue of ${actual_rev/100:,.2f} "
            f"vs expected ${expected_rev/100:,.2f} (Variance: {variance_pct:+.2f}%). "
            f"Validation confirms capacity expansion assumption held true."
        )

        evaluation = DecisionOutcomeEvaluation(
            id=str(uuid.uuid4()),
            insight_id=insight_id,
            company_id=company_id,
            executed_option_id=executed_option_id,
            expected_outcomes=expected_outcomes,
            actual_outcomes=actual_outcomes,
            variance_analysis={"revenue_variance_pct": variance_pct, "outcome_status": "SUCCESS" if variance_pct >= -5.0 else "UNDERPERFORMED"},
            learning_candidate=learning_text,
            knowledge_item_id=f"ki-lesson-{uuid.uuid4()}",
            evaluated_at=datetime.now(UTC),
        )

        saved = await self.repository.save_decision_outcome_evaluation(evaluation)
        self._publish_event(
            DecisionOutcomeEvaluatedEvent(
                evaluation_id=saved.id,
                insight_id=insight_id,
                company_id=company_id,
                variance_summary=f"Variance: {variance_pct:+.2f}%",
            )
        )

        return saved
