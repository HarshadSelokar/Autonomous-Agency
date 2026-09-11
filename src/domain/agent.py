"""
Agent Domain Entity and State Machine.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import InvalidStateTransitionError


class AgentState(str, Enum):
    IDLE = "IDLE"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


# Transition map defining valid source -> target state transitions
VALID_AGENT_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.IDLE: {AgentState.READY},
    AgentState.READY: {AgentState.RUNNING, AgentState.IDLE},
    AgentState.RUNNING: {
        AgentState.WAITING,
        AgentState.BLOCKED,
        AgentState.COMPLETED,
        AgentState.FAILED,
        AgentState.CANCELLED,
    },
    AgentState.WAITING: {AgentState.RUNNING, AgentState.FAILED, AgentState.CANCELLED},
    AgentState.BLOCKED: {AgentState.READY, AgentState.FAILED, AgentState.CANCELLED},
    AgentState.FAILED: {AgentState.READY, AgentState.IDLE},
    AgentState.CANCELLED: {AgentState.READY, AgentState.IDLE},
    AgentState.COMPLETED: {AgentState.READY, AgentState.IDLE},
}


@dataclass(frozen=True)
class ModelConfiguration:
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PermissionProfile:
    permissions: list[str] = field(default_factory=list)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "*" in self.permissions


@dataclass(frozen=True)
class VerificationPolicy:
    required: bool = False
    verifier_role: str | None = None


@dataclass(frozen=True)
class CommunicationPolicy:
    allowed_channels: list[str] = field(default_factory=list)
    restricted: bool = False


@dataclass
class Agent:
    id: str
    name: str
    role: str
    description: str = ""
    responsibilities: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    manager_id: str | None = None
    model_configuration: ModelConfiguration = field(default_factory=ModelConfiguration)
    permission_profile: PermissionProfile = field(default_factory=PermissionProfile)
    verification_policy: VerificationPolicy = field(default_factory=VerificationPolicy)
    communication_policy: CommunicationPolicy = field(default_factory=CommunicationPolicy)
    current_state: AgentState = AgentState.IDLE
    current_task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def can_transition_to(self, target_state: AgentState) -> bool:
        """Check if transition to target_state is allowed."""
        allowed_targets = VALID_AGENT_TRANSITIONS.get(self.current_state, set())
        return target_state in allowed_targets

    def transition_to(self, target_state: AgentState) -> None:
        """
        Transition agent state to target_state if valid, else raise InvalidStateTransitionError.
        """
        if self.current_state == target_state:
            return  # No-op if state remains unchanged

        if not self.can_transition_to(target_state):
            raise InvalidStateTransitionError(
                entity="Agent",
                entity_id=self.id,
                current_state=self.current_state.value,
                target_state=target_state.value,
            )

        self.current_state = target_state
        self.updated_at = datetime.now(UTC)
