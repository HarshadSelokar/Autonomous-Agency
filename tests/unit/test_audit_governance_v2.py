"""
Unit tests for Security, Governance & Audit 2.0 (Phase 40).
"""

import pytest
from src.application.audit_governance_v2 import AuditGovernanceV2Service
from src.domain.audit_v2 import AuditActionType


def test_audit_governance_hash_chain_and_verification():
    service = AuditGovernanceV2Service()
    tenant_id = "tenant-sec-1"

    # Record 3 actions
    rec1 = service.record_action(tenant_id, "user-1", AuditActionType.USER_AUTH, "/login")
    rec2 = service.record_action(tenant_id, "user-1", AuditActionType.WORKFLOW_EXECUTION, "workflow-123")
    rec3 = service.record_action(tenant_id, "user-1", AuditActionType.RESOURCE_ALLOCATION, "budget-456")

    assert rec1.prev_hash == "GENESIS"
    assert rec2.prev_hash == rec1.hash
    assert rec3.prev_hash == rec2.hash

    # Verify chain integrity
    assert service.verify_audit_chain(tenant_id) is True

    # Tamper with rec2
    rec2.details = {"tampered": True}
    assert service.verify_audit_chain(tenant_id) is False


def test_enforce_tenant_security_isolation():
    service = AuditGovernanceV2Service()
    tenant_a = "tenant-alpha"
    tenant_b = "tenant-beta"

    # Same tenant access allowed
    service.enforce_tenant_security(tenant_a, tenant_a)

    # Cross tenant access raises PermissionError and records violation
    with pytest.raises(PermissionError, match="Cross-tenant breach attempt blocked"):
        service.enforce_tenant_security(tenant_a, tenant_b, actor_id="malicious_user")

    trail = service.get_audit_trail(tenant_a)
    assert len(trail) == 1
    assert trail[0].action_type == AuditActionType.POLICY_VIOLATION


def test_concurrent_audit_writes_maintain_hash_chain_integrity():
    """Verifies SEC-03: Concurrent audit records maintain a single un-forked hash chain."""
    import concurrent.futures

    service = AuditGovernanceV2Service()
    tenant_id = "tenant-concurrent"

    def record_job(idx: int):
        service.record_action(
            tenant_id,
            f"user-{idx % 4}",
            AuditActionType.MODEL_INFERENCE,
            f"/resource/{idx}",
            {"step": idx},
        )

    # 40 concurrent operations across 8 worker threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(record_job, i) for i in range(40)]
        concurrent.futures.wait(futures)

    trail = service.get_audit_trail(tenant_id)
    assert len(trail) == 40
    # Complete cryptographic integrity check must pass without fork
    assert service.verify_audit_chain(tenant_id) is True
