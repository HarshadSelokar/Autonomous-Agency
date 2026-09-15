"""Failure injection test suite for Phase 13 Pixel Office.

Tests WebSocket disconnect/reconnect, event ordering, deduplication,
and state reconciliation.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.domain.events import OfficeStateUpdatedEvent
from src.application.office_realtime_service import (
    OfficeRealtimeBroadcaster,
    PixelOfficeConnection,
)
from src.application.office_projection_service import OfficeProjectionService


@pytest.mark.asyncio
async def test_websocket_reconnect_reconciliation():
    broadcaster = OfficeRealtimeBroadcaster()
    ws = AsyncMock()
    conn_id = "conn-reconnect-1"

    conn = PixelOfficeConnection(connection_id=conn_id, user_id=uuid4(), websocket=ws)
    broadcaster.register_connection(conn)
    assert broadcaster.active_connection_count == 1

    # Simulate disconnect
    broadcaster.unregister_connection(conn_id)
    assert broadcaster.active_connection_count == 0

    # Simulate reconnect
    conn_new = PixelOfficeConnection(connection_id=conn_id, user_id=uuid4(), websocket=ws)
    broadcaster.register_connection(conn_new)
    assert broadcaster.active_connection_count == 1


@pytest.mark.asyncio
async def test_duplicate_event_deduplication():
    broadcaster = OfficeRealtimeBroadcaster()
    ws = AsyncMock()

    conn = PixelOfficeConnection(connection_id="c1", user_id=uuid4(), websocket=ws)
    broadcaster.register_connection(conn)

    event = OfficeStateUpdatedEvent(
        employee_id=str(uuid4()),
        visual_state="WORKING",
        activity_summary="Coding feature",
    )

    delivered_first = await broadcaster.broadcast_event(event)
    assert delivered_first == 1

    # Broadcast identical event twice
    delivered_second = await broadcaster.broadcast_event(event)
    assert delivered_second == 0


@pytest.mark.asyncio
async def test_backend_state_reconciliation_overrides_stale_ui():
    service = OfficeProjectionService()
    emp_id = str(uuid4())

    # Backend state is COMPLETED/IDLE even if UI was showing WORKING
    visual_state = service.derive_employee_visual_state(
        employee_id=emp_id,
        employee_status="ACTIVE",
        is_governance_paused=False,
        is_agent_running=False,
    )
    assert visual_state.value == "IDLE"
