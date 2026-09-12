"""
Unit tests for Domain Events and EventDispatcher.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.event_dispatcher import EventDispatcher
from src.domain.events import (
    EmployeeCreatedEvent,
    EmployeeStatusChangedEvent,
)


@pytest.mark.asyncio
async def test_event_dispatcher_publishes_to_subscribers() -> None:
    dispatcher = EventDispatcher()
    handler = AsyncMock()

    dispatcher.subscribe(EmployeeCreatedEvent, handler)

    event = EmployeeCreatedEvent(
        employee_id="emp_1",
        employee_code="EMP-1",
        name="Alice",
        title="Engineer",
        role="developer",
        agent_id="agent_1",
    )

    await dispatcher.publish(event)

    handler.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_event_dispatcher_ignores_unsubscribed_events() -> None:
    dispatcher = EventDispatcher()
    handler = AsyncMock()

    dispatcher.subscribe(EmployeeCreatedEvent, handler)

    # Publish a different event type
    status_event = EmployeeStatusChangedEvent(employee_id="emp_1")
    await dispatcher.publish(status_event)

    handler.assert_not_called()
