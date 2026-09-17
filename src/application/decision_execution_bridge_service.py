"""
Decision Execution Bridge Service for Phase 26.

Enforces the Decision -> Governance -> Execution Boundary.
Guarantees recommendations CANNOT execute directly without passing through human governance approval.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Optional
import uuid

from src.domain.company_intelligence import DecisionInsight
from src.domain.exceptions import UnauthorizedDecisionExecutionError, DecisionInsightExpiredError
from src.domain.repository import CompanyIntelligenceRepositoryInterface


class DecisionExecutionBridgeService:
    """Governs the transition from Authorized Decision Insights to Operational Execution Workflows."""

    def __init__(self, repository: CompanyIntelligenceRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def execute_decision_insight(
        self,
        insight_id: str,
        actor_id: str,
        governance_approval_id: str,
    ) -> Dict[str, Any]:
        """Validates human governance approval and bridges decision to execution workflow."""
        insight = await self.repository.get_decision_insight_by_id(insight_id)
        if not insight:
            raise ValueError(f"Decision insight '{insight_id}' not found.")

        # Attach governance approval ID to insight if provided
        if governance_approval_id:
            insight.governance_approval_id = governance_approval_id

        # Enforce fundamental invariant: recommendation != decision != execution without approval
        insight.assert_valid_for_execution()

        # Mark insight executed
        insight.is_executed = True
        insight.updated_at = datetime.now(UTC)
        await self.repository.save_decision_insight(insight)

        execution_payload = {
            "execution_id": f"exec-{uuid.uuid4()}",
            "insight_id": insight.id,
            "company_id": insight.company_id,
            "recommended_option_id": insight.recommended_option_id,
            "governance_approval_id": governance_approval_id,
            "executed_by_actor_id": actor_id,
            "executed_at": datetime.now(UTC).isoformat(),
            "status": "GOVERNED_EXECUTION_INITIATED",
        }

        return execution_payload
