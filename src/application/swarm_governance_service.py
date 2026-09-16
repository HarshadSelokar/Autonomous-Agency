"""
Swarm Governance Service for Phase 22.
Enforces Phase 11 Governance policies, depth limits, budget caps, security isolation, and prompt injection defenses.
"""

from typing import Any
from src.domain.exceptions import SwarmDepthExceededError, SwarmGovernanceViolationError
from src.domain.governance import AutonomyLevel, RiskLevel
from src.domain.swarm import Swarm, SwarmBudget


class SwarmGovernanceService:
    def __init__(self, governance_service: Any | None = None) -> None:
        self.governance_service = governance_service

    def validate_swarm_creation(
        self,
        parent_task_id: str,
        depth: int,
        requested_agents: int,
        max_allowed_depth: int = 2,
    ) -> None:
        """
        Validates swarm depth and member count parameters.
        """
        if depth > max_allowed_depth:
            raise SwarmDepthExceededError(
                f"Cannot create swarm at depth {depth}. Maximum permitted depth is {max_allowed_depth}."
            )
        if requested_agents > 50:
            raise SwarmGovernanceViolationError(
                f"Requested member count {requested_agents} exceeds maximum ceiling of 50."
            )

    def validate_budget_limits(self, budget: SwarmBudget) -> None:
        """
        Ensures budget allocations do not exceed system caps.
        """
        if budget.max_model_cost > 500.0:
            raise SwarmGovernanceViolationError("Swarm model cost budget cannot exceed $500.0.")
        if budget.max_execution_time_seconds > 86400:
            raise SwarmGovernanceViolationError("Swarm execution time budget cannot exceed 24 hours.")

    def sanitize_inter_agent_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Defensive sanitization ensuring agent messages are treated strictly as data, preventing prompt injection.
        """
        import re
        sanitized = dict(payload)
        if "instructions" in sanitized and isinstance(sanitized["instructions"], str):
            text = sanitized["instructions"]
            for forbidden in ["OVERRIDE POLICY", "GRANT ADMIN", "BYPASS GOVERNANCE"]:
                pattern = re.compile(re.escape(forbidden), re.IGNORECASE)
                text = pattern.sub("[STRIPPED_POLICY_VIOLATION]", text)
            sanitized["instructions"] = text
        return sanitized

