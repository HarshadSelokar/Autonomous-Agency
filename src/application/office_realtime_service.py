"""Office Realtime Broadcaster Service.

Manages WebSocket connection subscriptions, authorization-filtered event projection,
and state reconciliation streams for the Pixel Office.
"""

import logging
from typing import Any
from uuid import UUID

from src.domain.events import OfficeStateUpdatedEvent

logger = logging.getLogger(__name__)


class PixelOfficeConnection:
    """Represents an active client WebSocket connection to the Pixel Office."""

    def __init__(
        self,
        connection_id: str,
        user_id: UUID,
        authorized_departments: list[str] | None = None,
        authorized_projects: list[UUID] | None = None,
        websocket: Any = None,
    ) -> None:
        self.connection_id = connection_id
        self.user_id = user_id
        self.authorized_departments = set(authorized_departments or [])
        self.authorized_projects = set(authorized_projects or [])
        self.websocket = websocket
        self.last_event_id: str | None = None

    def is_authorized_for_event(self, event: OfficeStateUpdatedEvent) -> bool:
        """Check if connection is authorized to receive event based on scopes."""
        proj_id_str = event.project_id
        if self.authorized_projects and proj_id_str:
            try:
                proj_id = UUID(proj_id_str)
                if proj_id not in self.authorized_projects:
                    return False
            except ValueError:
                pass

        return True


class OfficeRealtimeBroadcaster:
    """Manages real-time WebSocket connection lifecycle and event dispatch for Pixel Office."""

    def __init__(self) -> None:
        self._connections: dict[str, PixelOfficeConnection] = {}
        self._processed_event_ids: set[str] = set()

    def register_connection(self, connection: PixelOfficeConnection) -> None:
        """Register a new active WebSocket connection."""
        self._connections[connection.connection_id] = connection
        logger.info(f"Pixel Office WS connection registered: {connection.connection_id}")

    def unregister_connection(self, connection_id: str) -> None:
        """Unregister a disconnected WebSocket connection."""
        if connection_id in self._connections:
            del self._connections[connection_id]
            logger.info(f"Pixel Office WS connection unregistered: {connection_id}")

    @property
    def active_connection_count(self) -> int:
        """Return count of active client connections."""
        return len(self._connections)

    async def broadcast_event(self, event: OfficeStateUpdatedEvent) -> int:
        """Broadcast an office state update event to all authorized connections."""
        event_key = str(event.event_id)
        if event_key in self._processed_event_ids:
            logger.debug(f"Duplicate event ignored in Pixel Office broadcaster: {event_key}")
            return 0

        self._processed_event_ids.add(event_key)
        if len(self._processed_event_ids) > 10000:
            self._processed_event_ids.clear()

        delivered_count = 0
        event_data = {
            "event_id": event.event_id,
            "employee_id": event.employee_id,
            "visual_state": event.visual_state,
            "activity_summary": event.activity_summary,
            "task_id": event.task_id,
            "project_id": event.project_id,
            "occurred_at": event.occurred_at.isoformat() if hasattr(event.occurred_at, "isoformat") else str(event.occurred_at),
        }

        for conn in list(self._connections.values()):
            if conn.is_authorized_for_event(event):
                try:
                    if conn.websocket and hasattr(conn.websocket, "send_json"):
                        await conn.websocket.send_json(event_data)
                    delivered_count += 1
                except Exception as exc:
                    logger.warning(
                        f"Failed to deliver event {event_key} to connection {conn.connection_id}: {exc}"
                    )

        return delivered_count
