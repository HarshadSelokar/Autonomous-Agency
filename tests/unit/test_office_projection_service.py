"""Unit tests for OfficeProjectionService and OfficeRealtimeBroadcaster."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.office import (
    EmployeeVisualState,
    HumanAttentionType,
)
from src.domain.events import OfficeStateUpdatedEvent
from src.application.office_projection_service import OfficeProjectionService
from src.application.office_realtime_service import (
    OfficeRealtimeBroadcaster,
    PixelOfficeConnection,
)


def test_derive_employee_visual_state_precedence():
    service = OfficeProjectionService()
    emp_id = str(uuid4())

    # Governance paused supercedes everything
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
        is_governance_paused=True,
        is_recovering=True,
        is_awaiting_approval=True,
        is_agent_running=True,
    )
    assert state == EmployeeVisualState.PAUSED

    # Recovery supercedes approval/verifying/working
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
        is_governance_paused=False,
        is_recovering=True,
        is_awaiting_approval=True,
        is_agent_running=True,
    )
    assert state == EmployeeVisualState.RECOVERING

    # Approval supercedes verifying/working
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
        is_governance_paused=False,
        is_recovering=False,
        is_awaiting_approval=True,
        is_agent_running=True,
    )
    assert state == EmployeeVisualState.AWAITING_APPROVAL

    # Verifying supercedes blocked/working
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
        is_governance_paused=False,
        is_recovering=False,
        is_awaiting_approval=False,
        is_verifying=True,
        is_agent_running=True,
    )
    assert state == EmployeeVisualState.REVIEWING

    # Blocked supercedes working
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
        is_governance_paused=False,
        is_recovering=False,
        is_awaiting_approval=False,
        is_verifying=False,
        is_task_blocked=True,
        is_agent_running=True,
    )
    assert state == EmployeeVisualState.BLOCKED

    # Meeting supercedes working
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
        is_governance_paused=False,
        is_recovering=False,
        is_awaiting_approval=False,
        is_verifying=False,
        is_task_blocked=False,
        is_in_meeting=True,
        is_agent_running=True,
    )
    assert state == EmployeeVisualState.IN_MEETING

    # Working when agent running
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
        is_agent_running=True,
    )
    assert state == EmployeeVisualState.WORKING

    # Idle default
    state = service.derive_employee_visual_state(
        employee_id=emp_id,
    )
    assert state == EmployeeVisualState.IDLE


@pytest.mark.asyncio
async def test_build_company_overview():
    mock_emp_repo = AsyncMock()
    emp1 = MagicMock(
        id=uuid4(),
        name="Alice Dev",
        department_id=uuid4(),
        department_name="Engineering",
        title="Senior Developer",
        role="DEVELOPER",
        status="ACTIVE",
    )
    mock_emp_repo.list_all.return_value = [emp1]

    service = OfficeProjectionService(employee_repository=mock_emp_repo)
    org_id = str(uuid4())
    projection = await service.build_company_overview(org_id)

    assert projection.company_name == "Autonomous AI Organization"
    assert projection.active_employees_count == 1


@pytest.mark.asyncio
async def test_office_realtime_broadcaster():
    broadcaster = OfficeRealtimeBroadcaster()
    mock_ws = AsyncMock()

    conn = PixelOfficeConnection(
        connection_id="conn-1",
        user_id=uuid4(),
        authorized_departments=["Engineering"],
        websocket=mock_ws,
    )
    broadcaster.register_connection(conn)
    assert broadcaster.active_connection_count == 1

    event = OfficeStateUpdatedEvent(
        employee_id=str(uuid4()),
        visual_state="WORKING",
        activity_summary="Coding feature",
    )

    delivered = await broadcaster.broadcast_event(event)
    assert delivered == 1
    mock_ws.send_json.assert_called_once()

    # Test duplicate event deduplication
    delivered_dup = await broadcaster.broadcast_event(event)
    assert delivered_dup == 0

    broadcaster.unregister_connection("conn-1")
    assert broadcaster.active_connection_count == 0
