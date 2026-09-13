"""
ToolApprovalService Application Layer for Phase 8.
Handles creation, managerial review, approval, and rejection of consequential tool execution requests.
Enforces that an Agent CANNOT approve its own request or self-promote authority.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from src.domain.employee import Employee
from src.domain.repository import EmployeeRepositoryInterface
from src.domain.tool import (
    ApprovalStatus,
    ToolApproval,
    ToolCapability,
    ToolExecution,
    ToolExecutionStatus,
    ToolValidationError,
)


class UnauthorizedApprovalError(ToolValidationError):
    """Raised when an unauthorized actor attempts to approve a tool execution."""

    pass


class ToolApprovalService:
    def __init__(
        self,
        employee_repo: EmployeeRepositoryInterface | None = None,
        approval_repo: Any | None = None,
    ) -> None:
        self.employee_repo = employee_repo
        self.approval_repo = approval_repo
        self._in_memory_approvals: dict[str, ToolApproval] = {}

    async def create_approval_request(
        self,
        execution: ToolExecution,
        requester_employee_id: str,
    ) -> ToolApproval:
        """Create a pending ToolApproval record for a consequential tool execution."""
        approval_id = f"appr-{uuid.uuid4().hex[:8]}"
        approval = ToolApproval(
            id=approval_id,
            execution_id=execution.id,
            tool_id=execution.tool_id,
            capability=execution.capability,
            requester_employee_id=requester_employee_id,
            status=ApprovalStatus.PENDING,
        )
        if self.approval_repo:
            await self.approval_repo.save(approval)
        else:
            self._in_memory_approvals[approval_id] = approval
        return approval

    async def approve_request(
        self,
        approval_id: str,
        approver_employee_id: str,
        rationale: str | None = None,
    ) -> ToolApproval:
        """Managerial approval of a pending tool execution."""
        approval = await self._get_approval(approval_id)
        if not approval:
            raise ToolValidationError(f"ToolApproval '{approval_id}' not found.")

        # Invariant: Requester CANNOT approve their own tool request
        if approver_employee_id == approval.requester_employee_id:
            raise UnauthorizedApprovalError(
                f"Employee '{approver_employee_id}' cannot approve their own tool execution request!"
            )

        # Manager authority check
        if self.employee_repo:
            approver = await self.employee_repo.get_by_id(approver_employee_id)
            if not approver or not approver.is_executable():
                raise UnauthorizedApprovalError(f"Approver '{approver_employee_id}' not found or inactive.")
            is_mgr = approver.is_manager() if hasattr(approver, "is_manager") else False
            if not is_mgr:
                raise UnauthorizedApprovalError(
                    f"Employee '{approver.name}' ({approver_employee_id}) lacks managerial authority to approve tool execution."
                )

        approval.approve(approver_employee_id=approver_employee_id, rationale=rationale)
        if self.approval_repo:
            await self.approval_repo.save(approval)
        return approval

    async def reject_request(
        self,
        approval_id: str,
        approver_employee_id: str,
        rationale: str | None = None,
    ) -> ToolApproval:
        """Managerial rejection of a pending tool execution."""
        approval = await self._get_approval(approval_id)
        if not approval:
            raise ToolValidationError(f"ToolApproval '{approval_id}' not found.")

        approval.reject(approver_employee_id=approver_employee_id, rationale=rationale)
        if self.approval_repo:
            await self.approval_repo.save(approval)
        return approval

    async def _get_approval(self, approval_id: str) -> ToolApproval | None:
        if self.approval_repo:
            return await self.approval_repo.get_by_id(approval_id)
        return self._in_memory_approvals.get(approval_id)
