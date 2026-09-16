"""
Business Operations Governance Service Integration (Phase 23).

Binds high-trust financial operations to Phase 11 Governance policies,
risk classification, and human approval constraints.
"""

from typing import Any, Dict, Optional

from src.domain.governance import RiskLevel
from src.application.governance_service import GovernanceService
from src.domain.exceptions import UnauthorizedFinancialActionError


class BusinessGovernanceService:
    """Manages risk evaluation and approval enforcement for business actions."""

    def __init__(self, governance_service: Optional[GovernanceService] = None) -> None:
        self.governance_service = governance_service

    def classify_risk(self, action_type: str, amount_cents: int = 0) -> RiskLevel:
        """
        Classifies business operation risk deterministically.
        - LOW: read-only report, draft creation
        - MEDIUM: record expense/revenue, create invoice draft
        - HIGH: send invoice, approve procurement (< $50,000)
        - CRITICAL: execute external payment, approve large procurement (>= $50,000)
        """
        action_upper = action_type.upper()
        if "READ" in action_upper or "REPORT" in action_upper or "QUERY" in action_upper:
            return RiskLevel.LOW

        if action_upper in ("CREATE_DRAFT", "RECORD_REVENUE", "RECORD_EXPENSE", "DRAFT_INVOICE"):
            return RiskLevel.MEDIUM

        if action_upper in ("SEND_INVOICE", "APPROVE_PROCUREMENT", "CREATE_PURCHASE_ORDER"):
            if amount_cents >= 5_000_000:  # $50,000
                return RiskLevel.CRITICAL
            return RiskLevel.HIGH

        if action_upper in ("SUBMIT_PAYMENT", "EXECUTE_TRANSFER", "BANK_SETTLEMENT"):
            return RiskLevel.CRITICAL

        # Default fallback
        return RiskLevel.HIGH if amount_cents > 100_000 else RiskLevel.MEDIUM

    def evaluate_and_authorize(
        self,
        action_type: str,
        actor_id: str,
        amount_cents: int = 0,
        currency: str = "USD",
        approval_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RiskLevel:
        """
        Evaluates policy and verifies if required approvals are present.
        High/Critical actions require approval.
        """
        risk = self.classify_risk(action_type, amount_cents)

        if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not approval_id:
                raise UnauthorizedFinancialActionError(
                    f"Action '{action_type}' with risk level '{risk.value}' requires explicit governance approval."
                )

        return risk
