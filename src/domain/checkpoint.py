"""
AgentCheckpoint Domain Entity.
Represents a state snapshot for execution resumption and auditing.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AgentCheckpoint:
    id: str
    run_id: str
    current_state: str
    current_step: int
    context_reference: dict[str, Any] = field(default_factory=dict)
    output_so_far: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
