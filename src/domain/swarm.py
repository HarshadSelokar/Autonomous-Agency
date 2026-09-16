"""
Swarm Domain Model, Lifecycle State Machine, Value Objects, and Budget Entities for Phase 22.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid

from src.domain.exceptions import InvalidStateTransitionError, SwarmValidationError


class SwarmStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    FORMING = "FORMING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    COMPLETING = "COMPLETING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class CoordinationMode(str, Enum):
    PARALLEL = "PARALLEL"
    SEQUENTIAL = "SEQUENTIAL"
    PIPELINE = "PIPELINE"
    SPECIALIST = "SPECIALIST"
    DEBATE = "DEBATE"
    CONSENSUS = "CONSENSUS"
    REVIEW = "REVIEW"
    MAP_REDUCE = "MAP_REDUCE"
    HIERARCHICAL = "HIERARCHICAL"


class SwarmMemberStatus(str, Enum):
    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    WORKING = "WORKING"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    REMOVED = "REMOVED"


class SwarmMessageType(str, Enum):
    TASK_REQUEST = "TASK_REQUEST"
    TASK_RESULT = "TASK_RESULT"
    STATUS_UPDATE = "STATUS_UPDATE"
    BLOCKER = "BLOCKER"
    QUESTION = "QUESTION"
    CLARIFICATION_REQUEST = "CLARIFICATION_REQUEST"
    REVIEW_REQUEST = "REVIEW_REQUEST"
    REVIEW_RESULT = "REVIEW_RESULT"
    HANDOFF = "HANDOFF"
    ESCALATION = "ESCALATION"
    PROPOSAL = "PROPOSAL"
    CONSENSUS_REQUEST = "CONSENSUS_REQUEST"


VALID_SWARM_TRANSITIONS: dict[SwarmStatus, set[SwarmStatus]] = {
    SwarmStatus.CREATED: {SwarmStatus.PLANNING, SwarmStatus.CANCELLED},
    SwarmStatus.PLANNING: {SwarmStatus.FORMING, SwarmStatus.FAILED, SwarmStatus.CANCELLED},
    SwarmStatus.FORMING: {SwarmStatus.READY, SwarmStatus.FAILED, SwarmStatus.CANCELLED},
    SwarmStatus.READY: {SwarmStatus.RUNNING, SwarmStatus.CANCELLED},
    SwarmStatus.RUNNING: {
        SwarmStatus.PAUSED,
        SwarmStatus.DEGRADED,
        SwarmStatus.COMPLETING,
        SwarmStatus.FAILED,
        SwarmStatus.CANCELLED,
        SwarmStatus.ESCALATED,
    },
    SwarmStatus.PAUSED: {SwarmStatus.RUNNING, SwarmStatus.CANCELLED, SwarmStatus.ESCALATED},
    SwarmStatus.DEGRADED: {SwarmStatus.RUNNING, SwarmStatus.FAILED, SwarmStatus.ESCALATED, SwarmStatus.CANCELLED},
    SwarmStatus.COMPLETING: {SwarmStatus.VERIFYING, SwarmStatus.FAILED, SwarmStatus.CANCELLED},
    SwarmStatus.VERIFYING: {SwarmStatus.COMPLETED, SwarmStatus.FAILED, SwarmStatus.ESCALATED},
    SwarmStatus.COMPLETED: set(),
    SwarmStatus.FAILED: {SwarmStatus.PLANNING, SwarmStatus.CANCELLED, SwarmStatus.ESCALATED},
    SwarmStatus.CANCELLED: set(),
    SwarmStatus.ESCALATED: {SwarmStatus.PAUSED, SwarmStatus.RUNNING, SwarmStatus.CANCELLED},
}


@dataclass
class SwarmBudget:
    swarm_id: str
    max_execution_time_seconds: int = 3600
    max_model_cost: float = 50.0
    max_tool_calls: int = 200
    max_tokens: int = 500000
    max_retries: int = 5
    max_swarm_depth: int = 2
    
    current_execution_time_seconds: int = 0
    current_model_cost: float = 0.0
    current_tool_calls: int = 0
    current_tokens: int = 0
    current_retries: int = 0
    
    def is_exhausted(self) -> bool:
        return (
            self.current_execution_time_seconds >= self.max_execution_time_seconds
            or self.current_model_cost >= self.max_model_cost
            or self.current_tool_calls >= self.max_tool_calls
            or self.current_tokens >= self.max_tokens
            or self.current_retries >= self.max_retries
        )

    def record_usage(
        self,
        duration_seconds: int = 0,
        model_cost: float = 0.0,
        tool_calls: int = 0,
        tokens: int = 0,
        retries: int = 0,
    ) -> None:
        self.current_execution_time_seconds += duration_seconds
        self.current_model_cost += model_cost
        self.current_tool_calls += tool_calls
        self.current_tokens += tokens
        self.current_retries += retries


@dataclass
class SwarmMember:
    id: str
    swarm_id: str
    employee_id: str
    agent_id: str
    role: str
    capability: str
    assigned_task_id: str | None = None
    status: SwarmMemberStatus = SwarmMemberStatus.INVITED
    joined_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    left_at: datetime | None = None
    execution_stats: dict[str, Any] = field(default_factory=dict)

    def transition_to(self, new_status: SwarmMemberStatus) -> None:
        self.status = new_status
        if new_status in (SwarmMemberStatus.COMPLETED, SwarmMemberStatus.FAILED, SwarmMemberStatus.REMOVED):
            self.left_at = datetime.now(UTC)


@dataclass
class SwarmMessage:
    id: str
    swarm_id: str
    sender_id: str
    recipient_id: str | None
    task_id: str | None
    message_type: SwarmMessageType
    payload: dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SwarmConflict:
    id: str
    swarm_id: str
    task_id: str
    agent_a_id: str
    result_a: dict[str, Any]
    agent_b_id: str
    result_b: dict[str, Any]
    conflict_type: str
    resolution_strategy: str = "INDEPENDENT_VERIFICATION"
    resolved_result: dict[str, Any] | None = None
    is_resolved: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SwarmResult:
    id: str
    swarm_id: str
    parent_task_id: str
    member_results: dict[str, Any] = field(default_factory=dict)
    subtask_status: dict[str, str] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    disagreements: list[dict[str, Any]] = field(default_factory=list)
    unresolved_issues: list[str] = field(default_factory=list)
    aggregated_result: dict[str, Any] = field(default_factory=dict)
    aggregation_strategy: str = "DETERMINISTIC_MERGE"
    verification_status: str = "PENDING"
    is_completed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Swarm:
    id: str
    name: str
    code: str
    parent_task_id: str
    purpose: str
    manager_id: str
    objective_id: str | None = None
    project_id: str | None = None
    coordinator_member_id: str | None = None
    status: SwarmStatus = SwarmStatus.CREATED
    coordination_mode: CoordinationMode = CoordinationMode.PARALLEL
    depth: int = 1
    governance_context: dict[str, Any] = field(default_factory=dict)
    concurrency_limit: int = 5
    max_agents: int = 10
    members: list[SwarmMember] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    timeout_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition_to(self, new_status: SwarmStatus) -> None:
        allowed = VALID_SWARM_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                entity="Swarm",
                entity_id=self.id,
                current_state=self.status.value,
                target_state=new_status.value,
            )
        self.status = new_status
        now = datetime.now(UTC)
        if new_status == SwarmStatus.RUNNING and self.started_at is None:
            self.started_at = now
        elif new_status in (SwarmStatus.COMPLETED, SwarmStatus.FAILED, SwarmStatus.CANCELLED):
            self.completed_at = now


    def add_member(self, member: SwarmMember) -> None:
        if len(self.members) >= self.max_agents:
            raise SwarmValidationError(
                f"Cannot add member '{member.id}' to swarm '{self.id}': max_agents limit ({self.max_agents}) reached."
            )
        self.members.append(member)

    def get_member(self, member_id: str) -> SwarmMember | None:
        for m in self.members:
            if m.id == member_id:
                return m
        return None
