"""
WorkspaceAuthorizationService Application Layer for Phase 7.
Enforces strict workspace isolation boundaries and authorization checks.
"""

from typing import Any

from src.domain.workspace import Workspace, WorkspaceStatus, WorkspaceType, WorkspaceValidationError


class WorkspaceAccessDeniedError(WorkspaceValidationError):
    """Raised when an actor or Agent attempts unauthorized or cross-workspace access."""

    pass


class WorkspaceAuthorizationService:
    def __init__(self, workspace_repo: Any = None) -> None:
        self.workspace_repo = workspace_repo

    async def validate_task_workspace_access(
        self,
        workspace_id: str,
        current_task_id: str,
        actor_employee_id: str,
    ) -> Workspace:
        if not self.workspace_repo:
            raise ValueError("workspace_repo must be provided to fetch workspace by ID.")
        ws = await self.workspace_repo.get_by_id(workspace_id)
        if not ws:
            raise WorkspaceAccessDeniedError(f"Workspace '{workspace_id}' not found.")
        self.validate_access(ws, actor_employee_id=actor_employee_id, current_task_id=current_task_id)
        return ws

    def validate_access(
        self,
        workspace: Workspace,
        actor_employee_id: str,
        current_task_id: str | None = None,
        is_admin: bool = False,
    ) -> bool:
        """
        Validate workspace authorization and enforce strict boundary isolation.
        An Agent executing Task T1 MUST NOT access Workspace T2.
        """
        if workspace.status in {WorkspaceStatus.LOCKED, WorkspaceStatus.ARCHIVED, WorkspaceStatus.DESTROYED}:
            raise WorkspaceAccessDeniedError(
                f"Workspace '{workspace.name}' ({workspace.id}) is in non-accessible state '{workspace.status.value}'."
            )

        if is_admin:
            return True

        # Task Workspace Isolation Boundary
        if workspace.workspace_type == WorkspaceType.TASK:
            if current_task_id and workspace.task_id and current_task_id != workspace.task_id:
                raise WorkspaceAccessDeniedError(
                    f"Agent/Employee {actor_employee_id} assigned to Task {current_task_id} "
                    f"is DENIED access to isolated Workspace for Task {workspace.task_id}."
                )

        # Employee Workspace Isolation Boundary
        if workspace.workspace_type == WorkspaceType.EMPLOYEE:
            if workspace.employee_id and actor_employee_id != workspace.employee_id:
                raise WorkspaceAccessDeniedError(
                    f"Employee {actor_employee_id} is DENIED access to private Workspace owned by Employee {workspace.employee_id}."
                )

        return True
