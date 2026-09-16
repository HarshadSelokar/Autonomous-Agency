"""Security test suite for Phase 15 Dynamic Workforce Engine."""

from unittest.mock import AsyncMock

import pytest

from src.application.team_formation_service import TeamFormationService
from src.domain.workforce import (
    EmployeeTemplate,
    WorkforceChangeRequest,
    WorkforceChangeRequestType,
)


@pytest.fixture
def mock_team_repo():
    repo = AsyncMock()
    repo.get_by_code = AsyncMock(return_value=None)
    repo.save = AsyncMock(side_effect=lambda t: t)
    return repo


@pytest.fixture
def mock_workforce_repo():
    repo = AsyncMock()
    repo.save_change_request = AsyncMock(side_effect=lambda r: r)
    repo.get_change_request = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_employee_repo():
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda e: e)
    return repo


@pytest.mark.asyncio
async def test_prohibit_autonomous_employee_creation_without_governance(mock_team_repo, mock_workforce_repo, mock_employee_repo):
    """
    SECURITY TEST:
    An agent or system must NOT autonomously create/provision new workforce entities
    without explicit Human Governance approval.
    """
    service = TeamFormationService(mock_team_repo, mock_workforce_repo, mock_employee_repo)
    template = EmployeeTemplate(title="Senior Security Auditor", role="SECURITY", capabilities=["SECURITY"])

    # Attempting provisioning with is_human_approved=False and no governance_approval_id MUST fail
    with pytest.raises(ValueError, match="Autonomous employee provisioning prohibited"):
        await service.provision_employee_with_governance(
            template=template,
            name="Rogue Agent",
            department_id="dept-sec",
            governance_approval_id=None,
            is_human_approved=False,
        )


@pytest.mark.asyncio
async def test_prohibit_consequential_workforce_change_without_governance(mock_team_repo, mock_workforce_repo):
    """
    SECURITY TEST:
    Consequential workforce changes (e.g. REQUEST_NEW_EMPLOYEE) cannot be approved by normal agents.
    """
    service = TeamFormationService(mock_team_repo, mock_workforce_repo)

    req = WorkforceChangeRequest(
        request_type=WorkforceChangeRequestType.REQUEST_NEW_EMPLOYEE,
        target_id="template-sec",
        requested_by_id="agent-low-privilege",
        justification="Need extra headcount",
    )
    mock_workforce_repo.get_change_request = AsyncMock(return_value=req)

    with pytest.raises(ValueError, match="Human Governance approval"):
        await service.approve_workforce_change(
            change_request_id=req.id,
            actor_id="agent-low-privilege",
            governance_approval_id=None,
            is_human_approval=False,
        )
