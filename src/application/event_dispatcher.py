"""
In-memory Event Dispatcher for publishing and subscribing to Domain Events.
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from src.domain.events import DomainEvent

E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[Any], Awaitable[None]]


class EventDispatcher:
    def __init__(self) -> None:
        self._subscribers: dict[type[DomainEvent], list[Callable[[Any], Awaitable[None]]]] = (
            defaultdict(list)
        )

    def subscribe(
        self, event_type: type[E], handler: Callable[[E], Awaitable[None]]
    ) -> None:
        """Register an async event handler for a specific event type."""
        self._subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered subscribers."""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            await handler(event)
