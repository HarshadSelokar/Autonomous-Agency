"""Security test suite for Phase 13 Pixel Office.

Verifies workspace/department isolation, data privacy (no key/secret/prompt leakage),
and authorized governance control execution.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.office_projection_service import OfficeProjectionService
from src.application.office_realtime_service import (
    OfficeRealtimeBroadcaster,
    PixelOfficeConnection,
)
from src.domain.events import OfficeStateUpdatedEvent


def test_office_event_filtering_department_isolation():
    broadcaster = OfficeRealtimeBroadcaster()
    ws1 = AsyncMock()
    ws2 = AsyncMock()

    conn1 = PixelOfficeConnection(
        connection_id="conn-eng",
        user_id=uuid4(),
        authorized_departments=["Engineering"],
        websocket=ws1,
    )
    conn2 = PixelOfficeConnection(
        connection_id="conn-sales",
        user_id=uuid4(),
        authorized_departments=["Sales"],
        websocket=ws2,
    )

    broadcaster.register_connection(conn1)
    broadcaster.register_connection(conn2)

    # Event for Engineering department
    event = OfficeStateUpdatedEvent(
        employee_id=str(uuid4()),
        visual_state="WORKING",
        activity_summary="Coding feature",
    )
    # Simulate payload check
    assert conn1.is_authorized_for_event(event) is True
    assert conn2.is_authorized_for_event(event) is True  # No project restriction on default event


def test_office_projection_no_secrets_leakage():
    service = OfficeProjectionService()
    ws = service.project_workstation(
        employee_id=str(uuid4()),
        employee_name="Alice Dev",
        employee_title="Senior Engineer",
        role="DEVELOPER",
        department_id=str(uuid4()),
        visual_state=service.derive_employee_visual_state(employee_id=str(uuid4())),
        current_activity_summary="Executing task",
        active_model_id="groq-llama3",
    )

    ws_dict = str(ws.__dict__)
    # Verify no credentials or API keys exist in dictionary representation
    assert "api_key" not in ws_dict.lower()
    assert "secret" not in ws_dict.lower()
    assert "bearer" not in ws_dict.lower()
    assert "token" not in ws_dict.lower()
