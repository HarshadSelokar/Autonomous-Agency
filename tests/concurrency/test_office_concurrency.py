"""Concurrency test suite for Phase 13 Pixel Office.

Tests simultaneous employee updates, rapid state transitions, and governance races.
"""

import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.office_realtime_service import (
    OfficeRealtimeBroadcaster,
    PixelOfficeConnection,
)
from src.domain.events import OfficeStateUpdatedEvent


@pytest.mark.asyncio
async def test_simultaneous_event_broadcast():
    broadcaster = OfficeRealtimeBroadcaster()
    ws = AsyncMock()
    conn = PixelOfficeConnection(connection_id="c-conc", user_id=uuid4(), websocket=ws)
    broadcaster.register_connection(conn)

    events = [
        OfficeStateUpdatedEvent(
            employee_id=str(uuid4()),
            visual_state="WORKING",
            activity_summary=f"Task {i}",
        )
        for i in range(20)
    ]

    results = await asyncio.gather(*[broadcaster.broadcast_event(evt) for evt in events])
    assert sum(results) == 20
    assert ws.send_json.call_count == 20
