"""
ResilienceV2Engine application service (Phase 39 - Advanced Reliability, Recovery & Self-Healing).
Provides automated fault classification, circuit breaker tracking, recovery strategies, and tenant-isolated self-healing.
"""

from collections import defaultdict
from typing import Any
from src.domain.resilience_v2 import (
    FaultSeverity,
    RecoveryActionType,
    ResilienceV2Policy,
    SelfHealingAction,
)


class ResilienceV2Engine:
    def __init__(self, repository=None):
        self.repository = repository
        self._policies: dict[str, ResilienceV2Policy] = {}
        self._fault_counters: dict[str, int] = defaultdict(int)
        self._history: list[SelfHealingAction] = []

    def get_policy(self, tenant_id: str) -> ResilienceV2Policy:
        if tenant_id not in self._policies and self.repository:
            stored = self.repository.get_policy(tenant_id)
            if stored is not None:
                self._policies[tenant_id] = stored
        if tenant_id not in self._policies:
            import uuid
            policy = ResilienceV2Policy(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                max_retries=3,
                circuit_breaker_threshold=5,
                auto_self_healing=True,
            )
            self._policies[tenant_id] = policy
            if self.repository:
                self.repository.save_policy(policy)
        return self._policies[tenant_id]

    def set_policy(self, policy: ResilienceV2Policy) -> None:
        self._policies[policy.tenant_id] = policy
        if self.repository:
            self.repository.save_policy(policy)

    def handle_fault(self, tenant_id: str, fault_type: str, details: dict[str, Any] | None = None) -> SelfHealingAction:
        policy = self.get_policy(tenant_id)
        if self.repository and tenant_id not in self._fault_counters:
            # Faults recorded by earlier processes count toward the circuit breaker too
            self._fault_counters[tenant_id] = self.repository.count_faults(tenant_id)
        self._fault_counters[tenant_id] += 1
        fault_count = self._fault_counters[tenant_id]

        # Determine severity & action strategy
        if "rate_limit" in fault_type.lower() or "timeout" in fault_type.lower():
            severity = FaultSeverity.MINOR
            action_type = RecoveryActionType.RETRY if fault_count <= policy.max_retries else RecoveryActionType.FALLBACK_MODEL
        elif "model_error" in fault_type.lower():
            severity = FaultSeverity.MODERATE
            action_type = RecoveryActionType.FALLBACK_MODEL
        elif fault_count >= policy.circuit_breaker_threshold:
            severity = FaultSeverity.CRITICAL
            action_type = RecoveryActionType.ISOLATE_TENANT
        else:
            severity = FaultSeverity.MODERATE
            action_type = RecoveryActionType.RESTART_AGENT

        action = SelfHealingAction(
            tenant_id=tenant_id,
            fault_type=fault_type,
            severity=severity,
            action_taken=action_type,
            success=True,
            details=details or {"fault_count": fault_count},
        )
        self._history.append(action)

        if self.repository:
            self.repository.save_self_healing_action(action)

        return action

    def reset_fault_counter(self, tenant_id: str) -> None:
        self._fault_counters[tenant_id] = 0
