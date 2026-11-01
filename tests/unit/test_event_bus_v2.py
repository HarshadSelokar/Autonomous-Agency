"""
Unit tests for Event-Driven Autonomous Operations (Phase 38).
"""

from src.application.event_bus_v2 import EventBusV2
from src.domain.event_v2 import EventV2, EventPriority, OutboxStatus


def test_event_bus_pub_sub():
    bus = EventBusV2()
    received_events = []

    def handle_agent_completed(evt: EventV2):
        received_events.append(evt)

    bus.subscribe("agent.task.completed", handle_agent_completed)

    event = EventV2(
        tenant_id="tenant-100",
        event_type="agent.task.completed",
        payload={"task_id": "task-abc", "status": "SUCCESS"},
        priority=EventPriority.HIGH,
    )
    bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].tenant_id == "tenant-100"
    assert received_events[0].payload["task_id"] == "task-abc"


def test_event_bus_transactional_outbox():
    bus = EventBusV2()
    received_events = []

    bus.subscribe("workflow.node.failed", lambda evt: received_events.append(evt))

    outbox_msg = bus.publish_outbox(
        tenant_id="tenant-200",
        event_type="workflow.node.failed",
        payload={"node_id": "step-3", "error": "timeout"},
    )

    assert outbox_msg.status == OutboxStatus.PENDING
    assert len(received_events) == 0

    processed = bus.process_outbox()
    assert processed == 1
    assert outbox_msg.status == OutboxStatus.PROCESSED
    assert len(received_events) == 1
    assert received_events[0].tenant_id == "tenant-200"
