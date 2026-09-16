"""
ToolPolicyEngine Application Layer for Phase 8.
Evaluates organizational tool policies based on actor, employee role, capability, risk level, and workspace context.
Deterministic decision outputs: ALLOW, REQUIRE_APPROVAL, DENY.
"""

from enum import Enum

from src.domain.employee import Employee
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolDefinition,
    ToolRequest,
    ToolRiskLevel,
)


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class ToolPolicyEngine:
    def evaluate(
        self,
        tool: ToolDefinition,
        request: ToolRequest,
        actor_employee: Employee | None = None,
    ) -> PolicyDecision:
        """
        Evaluate organizational policy rules for a tool request.
        Backend-controlled policy evaluation prevents LLM model permission escalation.
        """
        # 1. Base Permission Mode Rules
        if tool.permission_mode == PermissionMode.BLOCKED:
            return PolicyDecision.DENY

        if tool.permission_mode == PermissionMode.APPROVAL:
            return PolicyDecision.REQUIRE_APPROVAL

        # 2. Risk Level Evaluation
        if tool.risk_level in {ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL}:
            is_manager = actor_employee.is_manager() if (actor_employee and hasattr(actor_employee, "is_manager")) else False
            if not is_manager:
                return PolicyDecision.REQUIRE_APPROVAL

        # 3. High-Risk Capabilities (DELETE_FILE, DATABASE_WRITE, GIT_WRITE)
        high_risk_caps = {
            ToolCapability.DELETE_FILE,
            ToolCapability.DATABASE_WRITE,
            ToolCapability.GIT_WRITE,
        }
        if request.requested_capability in high_risk_caps:
            is_manager = actor_employee.is_manager() if (actor_employee and hasattr(actor_employee, "is_manager")) else False
            if not is_manager:
                return PolicyDecision.REQUIRE_APPROVAL

        return PolicyDecision.ALLOW
