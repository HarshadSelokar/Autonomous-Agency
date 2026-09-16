"""Failure injection test suite for Phase 15 Dynamic Workforce Engine."""

from unittest.mock import AsyncMock

import pytest

from src.application.team_formation_service import TeamFormationService
from src.application.workforce_planning_service import WorkforcePlanningService
from src.domain.employee import Employee, EmployeeStatus
from src.domain.team import Team, TeamStatus
from src.domain.workforce import WorkforceDemand


@pytest.fixture
def mock_workforce_repo():
    repo = AsyncMock()
    repo.save_demand = AsyncMock(side_effect=lambda d: d)
    repo.save_recommendation = AsyncMock(side_effect=lambda r: r)
    return repo


@pytest.fixture
def mock_team_repo():
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda t: t)
    return repo


@pytest.mark.asyncio
async def test_no_qualified_employee_fallback(mock_workforce_repo):
    """
    FAILURE INJECTION:
    When no candidate possesses the requested capability, the recommendation engine
    must handle zero candidates gracefully, report 0 candidates, and generate explainable reasoning.
    """
    service = WorkforcePlanningService(mock_workforce_repo)
    demand = WorkforceDemand(source_type="PROJECT", source_id="p1", capability="QUANTUM_CRYPTOGRAPHY", required_count=1)

    emp = Employee(
        id="emp-1",
        employee_code="EMP-1",
        name="Alice",
        title="Web Developer",
        role="ENGINEER",
        agent_id="agent-1",
        status=EmployeeStatus.ACTIVE,
        capabilities=["FRONTEND_DEVELOPMENT"],
    )

    rec = await service.generate_staffing_recommendation(
        demand=demand,
        all_employees=[emp],
    )
    assert len(rec.candidate_employee_ids) == 0
    assert rec.final_score == 0.0
    assert "WARNING: Capability gap remaining" in rec.reasoning


@pytest.mark.asyncio
async def test_inactive_employee_assignment_rejection(mock_team_repo, mock_workforce_repo):
    """
    FAILURE INJECTION:
    Attempting to assign an inactive/suspended employee to a team MUST be rejected.
    """
    service = TeamFormationService(mock_team_repo, mock_workforce_repo)

    team = Team(name="Project X", code="PX", status=TeamStatus.PROPOSED)
    mock_team_repo.get_by_id = AsyncMock(return_value=team)

    suspended_emp = Employee(
        id="emp-suspended",
        employee_code="EMP-S",
        name="Suspended Bob",
        title="Engineer",
        role="ENGINEER",
        agent_id="agent-s",
        status=EmployeeStatus.SUSPENDED,
        capabilities=["BACKEND_DEVELOPMENT"],
    )

    with pytest.raises(ValueError, match="Cannot assign inactive/suspended employee"):
        await service.form_team(
            team_id=team.id,
            member_employees=[(suspended_emp, "MEMBER", 100.0)],
        )
