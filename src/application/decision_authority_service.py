"""
DecisionAuthorityService Application Layer for Phase 6.
Enforces strict decision approval authority validation, actor identity verification,
and the LLM authority boundary (LLM proposes, Human/Manager decides).
"""

from src.domain.decision import Decision, DecisionProvenance, DecisionStatus, DecisionValidationError
from src.domain.employee import Employee
from src.domain.exceptions import ObjectiveValidationError
from src.domain.repository import EmployeeRepositoryInterface


class UnauthorizedDecisionApprovalError(ObjectiveValidationError):
    """Raised when an unauthorized actor attempts to approve or reject a decision."""

    pass


class DecisionAuthorityService:
    def __init__(self, employee_repo: EmployeeRepositoryInterface) -> None:
        self.employee_repo = employee_repo

    async def validate_approver_authority(
        self,
        decision: Decision,
        approver_employee_id: str,
    ) -> Employee:
        """Validate that the approving actor exists, is ACTIVE, and possesses decision authority."""
        if not approver_employee_id or not approver_employee_id.strip():
            raise UnauthorizedDecisionApprovalError("Approver employee ID cannot be empty.")

        approver = await self.employee_repo.get_by_id(approver_employee_id)
        if not approver or approver.status.value != "ACTIVE":
            raise UnauthorizedDecisionApprovalError(
                f"Approver employee {approver_employee_id} not found or inactive."
            )

        # Enforce Managerial / Role Authority:
        # If decision requires managerial authority or approving_authority_role is specified
        if decision.approving_authority_role:
            req_role = decision.approving_authority_role.lower()
            actual_role = (approver.role or "").lower()
            actual_title = (approver.title or "").lower()
            is_mgr = "manager" in actual_role or "manager" in actual_title or "lead" in actual_role
            if req_role not in actual_role and req_role not in actual_title and not is_mgr:
                raise UnauthorizedDecisionApprovalError(
                    f"Employee '{approver.name}' ({approver_employee_id}) with role '{approver.role}' "
                    f"lacks required approving authority role '{decision.approving_authority_role}'."
                )

        return approver

    async def submit_for_review(self, decision: Decision) -> Decision:
        """Transition decision from PROPOSED to UNDER_REVIEW."""
        decision.transition_to(DecisionStatus.UNDER_REVIEW)
        return decision

    async def approve_decision(
        self,
        decision: Decision,
        approver_employee_id: str,
        provenance: DecisionProvenance | None = None,
    ) -> Decision:
        """Approve a decision after strict authority validation."""
        approver = await self.validate_approver_authority(decision, approver_employee_id)

        # Move to UNDER_REVIEW first if still PROPOSED
        if decision.status == DecisionStatus.PROPOSED:
            decision.transition_to(DecisionStatus.UNDER_REVIEW)

        if provenance:
            decision.provenance = provenance

        decision.transition_to(
            DecisionStatus.APPROVED,
            approver_employee_id=approver.id,
            approver_role=approver.title or approver.role,
        )
        return decision

    async def reject_decision(
        self,
        decision: Decision,
        approver_employee_id: str,
        reason: str,
    ) -> Decision:
        """Reject a decision after strict authority validation."""
        await self.validate_approver_authority(decision, approver_employee_id)
        if decision.status == DecisionStatus.PROPOSED:
            decision.transition_to(DecisionStatus.UNDER_REVIEW)

        decision.rationale = f"REJECTED by {approver_employee_id}: {reason}"
        decision.transition_to(DecisionStatus.REJECTED)
        return decision
