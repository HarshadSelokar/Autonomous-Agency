"""Unit tests for TeamFormationService."""

import pytest
from unittest.mock import AsyncMock

from src.application.team_formation_service import TeamFormationService
from src.domain.employee import Employee, EmployeeStatus
from src.domain.team import Team, TeamStatus, TeamType
from src.domain.workforce import (
    EmployeeTemplate,
    WorkforceChangeRequest,
    WorkforceChangeRequestStatus,
    WorkforceChangeRequestType,
)


@pytest.fixture
def mock_team_repo():
    repo = AsyncMock()
    repo.get_by_code = AsyncMock(return_value=None)
    repo.save = AsyncMock(side_effect=lambda t: t)
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_workforce_repo():
    repo = AsyncMock()
    repo.save_change_request = AsyncMock(side_effect=lambda r: r)
    repo.get_change_request = AsyncMock(return_value=None)
    repo.save_decision = AsyncMock(side_effect=lambda d: d)
    repo.save_allocation = AsyncMock(side_effect=lambda a: a)
    repo.list_allocations = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_employee_repo():
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda e: e)
    return repo


@pytest.mark.asyncio
async def test_propose_and_form_team(mock_team_repo, mock_workforce_repo):
    service = TeamFormationService(mock_team_repo, mock_workforce_repo)

    team = await service.propose_team(
        name="Apollo Team",
        code="APL",
        purpose="Lunar Mission",
        team_type=TeamType.PROJECT,
    )
    assert team.status == TeamStatus.PROPOSED
    assert team.code == "APL"

    # Set up get_by_id mock
    mock_team_repo.get_by_id = AsyncMock(return_value=team)

    emp = Employee(
        id="emp-1",
        employee_code="EMP-1",
        name="Charlie",
        title="Software Engineer",
        role="ENGINEER",
        agent_id="agent-1",
        status=EmployeeStatus.ACTIVE,
        capabilities=["BACKEND_DEVELOPMENT"],
    )

    formed_team = await service.form_team(
        team_id=team.id,
        member_employees=[(emp, "LEAD", 100.0)],
        manager_id="mgr-1",
    )

    assert formed_team.status == TeamStatus.ACTIVE
    assert len(formed_team.members) == 1
    assert "BACKEND_DEVELOPMENT" in formed_team.capabilities


@pytest.mark.asyncio
async def test_governed_workforce_change(mock_team_repo, mock_workforce_repo):
    service = TeamFormationService(mock_team_repo, mock_workforce_repo)

    req = await service.request_workforce_change(
        request_type=WorkforceChangeRequestType.REQUEST_NEW_EMPLOYEE,
        target_id="template-1",
        requested_by_id="mgr-1",
        justification="Critical QA capacity gap",
    )
    assert req.status == WorkforceChangeRequestStatus.PENDING

    mock_workforce_repo.get_change_request = AsyncMock(return_value=req)

    # Attempt approval without human governance approval should fail for consequential change
    with pytest.raises(ValueError, match="Human Governance approval"):
        await service.approve_workforce_change(
            change_request_id=req.id,
            actor_id="agent-mgr",
            is_human_approval=False,
        )

    # Approval with human governance approval succeeds
    decision = await service.approve_workforce_change(
        change_request_id=req.id,
        actor_id="human-admin",
        is_human_approval=True,
    )
    assert decision.decision_type == "APPROVED"
    assert req.status == WorkforceChangeRequestStatus.APPROVED


@pytest.mark.asyncio
async def test_provision_employee_with_governance(mock_team_repo, mock_workforce_repo, mock_employee_repo):
    service = TeamFormationService(mock_team_repo, mock_workforce_repo, mock_employee_repo)

    tpl = EmployeeTemplate(
        title="DevOps Engineer",
        role="ENGINEER",
        capabilities=["DEVOPS"],
    )

    # Autonomous provisioning without governance fails
    with pytest.raises(ValueError, match="prohibited"):
        await service.provision_employee_with_governance(
            template=tpl,
            name="Eve",
            department_id="dept-devops",
            is_human_approved=False,
        )

    # Governed provisioning succeeds
    emp = await service.provision_employee_with_governance(
        template=tpl,
        name="Eve",
        department_id="dept-devops",
        is_human_approved=True,
    )
    assert emp.name == "Eve"
    assert "DEVOPS" in emp.capabilities
    mock_employee_repo.save.assert_called_once()
