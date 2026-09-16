"""
Unit tests for Team domain entities.
"""

import pytest

from src.domain.team import Team, TeamStatus, TeamType


def test_team_lifecycle():
    team = Team(
        name="Phoenix Squad",
        code="PHX",
        purpose="Platform Overhaul",
        team_type=TeamType.TEMPORARY,
    )
    assert team.status == TeamStatus.PROPOSED

    team.activate()
    assert team.status == TeamStatus.ACTIVE

    team.start_dissolving()
    assert team.status == TeamStatus.DISSOLVING

    team.dissolve()
    assert team.status == TeamStatus.DISSOLVED
    assert team.dissolved_at is not None


def test_team_member_management():
    team = Team(name="Alpha", code="ALP")
    team.activate()

    member = team.add_member(employee_id="emp-1", role_in_team="LEAD", allocation_percentage=100.0)
    assert member.employee_id == "emp-1"
    assert member.role_in_team == "LEAD"
    assert len(team.members) == 1

    # Adding duplicate active member raises error
    with pytest.raises(ValueError):
        team.add_member(employee_id="emp-1")

    # Remove member
    team.remove_member("emp-1")
    assert member.removed_at is not None

    # Removing non-active member raises error
    with pytest.raises(ValueError):
        team.remove_member("emp-1")


def test_invalid_team_activation():
    team = Team(name="Beta")
    team.dissolve()
    with pytest.raises(ValueError):
        team.activate()
