"""
Domain layer typed exceptions for Agent Runtime.
"""


class DomainError(Exception):
    """Base class for all domain-level errors."""

    pass


class InvalidStateTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, entity: str, entity_id: str, current_state: str, target_state: str) -> None:
        self.entity = entity
        self.entity_id = entity_id
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            f"Invalid state transition for {entity} '{entity_id}': "
            f"cannot transition from '{current_state}' to '{target_state}'."
        )


class AgentNotFoundError(DomainError):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent with ID '{agent_id}' was not found.")


class AgentValidationError(DomainError):
    """Raised when agent data fails domain validation."""

    pass
