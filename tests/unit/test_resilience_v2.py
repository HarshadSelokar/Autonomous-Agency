"""
Unit tests for Advanced Reliability, Recovery & Self-Healing (Phase 39).
"""

from src.application.resilience_v2_engine import ResilienceV2Engine
from src.domain.resilience_v2 import FaultSeverity, RecoveryActionType


def test_resilience_v2_fault_handling_and_self_healing():
    engine = ResilienceV2Engine()
    tenant_id = "tenant-res-1"

    # Test minor timeout fault -> RETRY
    act1 = engine.handle_fault(tenant_id=tenant_id, fault_type="timeout_error")
    assert act1.severity == FaultSeverity.MINOR
    assert act1.action_taken == RecoveryActionType.RETRY

    # Trigger circuit breaker threshold -> ISOLATE_TENANT
    for _ in range(4):
        act = engine.handle_fault(tenant_id=tenant_id, fault_type="fatal_system_crash")

    assert act.severity == FaultSeverity.CRITICAL
    assert act.action_taken == RecoveryActionType.ISOLATE_TENANT


def test_resilience_v2_model_fallback():
    engine = ResilienceV2Engine()
    tenant_id = "tenant-res-2"

    act = engine.handle_fault(tenant_id=tenant_id, fault_type="model_error_500")
    assert act.action_taken == RecoveryActionType.FALLBACK_MODEL
