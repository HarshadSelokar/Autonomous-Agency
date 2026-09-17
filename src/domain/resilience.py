"""
Domain models for Phase 30 Production Hardening, Circuit Breakers, Security & Enterprise Resilience.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class CircuitBreakerState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class DegradationState(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    RECOVERING = "RECOVERING"


class SecurityIncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    CONTAINING = "CONTAINING"
    CONTAINED = "CONTAINED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SecuritySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class CircuitBreaker:
    id: str = field(default_factory=lambda: f"cb-{uuid.uuid4().hex[:8]}")
    name: str = ""
    dependency_name: str = ""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_threshold: int = 5
    recovery_time_seconds: int = 60
    failure_count: int = 0
    success_count: int = 0
    last_failure_at: Optional[datetime] = None
    last_state_change_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    initial_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_categories: List[str] = field(default_factory=lambda: ["TIMEOUT", "NETWORK_FAILURE", "RATE_LIMIT"])


@dataclass
class TimeoutPolicy:
    timeout_seconds: float = 30.0
    action_on_timeout: str = "CANCEL_AND_FALLBACK"


@dataclass
class ResiliencePolicy:
    id: str = field(default_factory=lambda: f"respol-{uuid.uuid4().hex[:8]}")
    target_name: str = ""
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_policy: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    circuit_breaker_enabled: bool = True
    fallback_enabled: bool = True
    degradation_behavior: DegradationState = DegradationState.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SecuritySignal:
    id: str = field(default_factory=lambda: f"secsig-{uuid.uuid4().hex[:8]}")
    source: str = ""
    signal_type: str = "PROMPT_INJECTION_ATTEMPT"
    severity: SecuritySeverity = SecuritySeverity.HIGH
    raw_content: str = ""
    sanitized_content: str = ""
    is_blocked: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SecurityIncident:
    id: str = field(default_factory=lambda: f"secinc-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    severity: SecuritySeverity = SecuritySeverity.HIGH
    status: SecurityIncidentStatus = SecurityIncidentStatus.DETECTED
    affected_components: List[str] = field(default_factory=list)
    governance_approval_id: Optional[str] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: Optional[datetime] = None


@dataclass
class AuditTrailLog:
    id: str = field(default_factory=lambda: f"audit-{uuid.uuid4().hex[:8]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    actor_id: str = ""
    actor_type: str = "AGENT"
    enterprise_id: Optional[str] = None
    company_id: Optional[str] = None
    action: str = ""
    resource: str = ""
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    checksum: str = ""
    correlation_id: str = field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:8]}")


@dataclass
class DependencyHealthSnapshot:
    id: str = field(default_factory=lambda: f"dephealth-{uuid.uuid4().hex[:8]}")
    dependency_name: str = ""
    is_available: bool = True
    latency_ms: float = 12.5
    error_rate_pct: float = 0.0
    circuit_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    last_checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProductionReadinessItem:
    id: str = field(default_factory=lambda: f"readi-{uuid.uuid4().hex[:8]}")
    domain: str = ""
    requirement: str = ""
    status: str = "PASSED"
    evidence_reference: str = ""
    tested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
