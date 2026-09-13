"""
Unit tests for Workspace domain entity, lifecycle state transitions, and authorization isolation.
"""

import pytest

from src.application.workspace_authorization_service import (
    WorkspaceAccessDeniedError,
    WorkspaceAuthorizationService,
)
from src.domain.workspace import (
    Workspace,
    WorkspaceStateError,
    WorkspaceStatus,
    WorkspaceType,
    WorkspaceValidationError,
)


def test_workspace_creation_and_validation() -> None:
    ws = Workspace(
        id="ws-100",
        name="Task T-1 Workspace",
        workspace_type=WorkspaceType.TASK,
        owner_id="TASK:t-100",
        task_id="t-100",
    )
    assert ws.id == "ws-100"
    assert ws.status == WorkspaceStatus.CREATED
    assert ws.workspace_type == WorkspaceType.TASK


def test_workspace_lifecycle_transitions() -> None:
    ws = Workspace(
        id="ws-200",
        name="Project P-1 Workspace",
        workspace_type=WorkspaceType.PROJECT,
        owner_id="PROJECT:p-1",
    )
    ws.transition_to(WorkspaceStatus.ACTIVE)
    assert ws.status == WorkspaceStatus.ACTIVE

    ws.transition_to(WorkspaceStatus.LOCKED)
    assert ws.status == WorkspaceStatus.LOCKED

    ws.transition_to(WorkspaceStatus.ARCHIVED)
    assert ws.status == WorkspaceStatus.ARCHIVED


def test_workspace_cross_task_isolation_denied() -> None:
    auth_service = WorkspaceAuthorizationService()

    ws_t1 = Workspace(
        id="ws-task-1",
        name="Task 1 Workspace",
        workspace_type=WorkspaceType.TASK,
        owner_id="TASK:t-1",
        task_id="t-1",
        status=WorkspaceStatus.ACTIVE,
    )

    # Access by agent assigned to Task 1 succeeds
    assert auth_service.validate_access(ws_t1, actor_employee_id="emp-dev", current_task_id="t-1") is True

    # Access by agent assigned to Task 2 fails with WorkspaceAccessDeniedError
    with pytest.raises(WorkspaceAccessDeniedError, match="DENIED access to isolated Workspace"):
        auth_service.validate_access(ws_t1, actor_employee_id="emp-dev", current_task_id="t-2")


def test_workspace_locked_state_denied() -> None:
    auth_service = WorkspaceAuthorizationService()
    ws = Workspace(
        id="ws-locked",
        name="Locked Workspace",
        workspace_type=WorkspaceType.TASK,
        owner_id="TASK:t-1",
        task_id="t-1",
        status=WorkspaceStatus.LOCKED,
    )

    with pytest.raises(WorkspaceAccessDeniedError, match="is in non-accessible state 'LOCKED'"):
        auth_service.validate_access(ws, actor_employee_id="emp-dev", current_task_id="t-1")
