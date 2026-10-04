"""
Domain entities for Advanced Reliability, Recovery & Self-Healing (Phase 39).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid


class FaultSeverity(str, Enum):
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class RecoveryActionType(str, Enum):
    RETRY = "RETRY"
    FALLBACK_MODEL = "FALLBACK_MODEL"
    RESTART_AGENT = "RESTART_AGENT"
    ISOLATE_TENANT = "ISOLATE_TENANT"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"


@dataclass
class ResilienceV2Policy:
    id: str
    tenant_id: str
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    auto_self_healing: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SelfHealingAction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    fault_type: str = ""
    severity: FaultSeverity = FaultSeverity.MODERATE
    action_taken: RecoveryActionType = RecoveryActionType.RETRY
    success: bool = True
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
