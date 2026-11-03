"""
AuditGovernanceV2Service application service (Phase 40 - Security, Governance & Audit 2.0).
Provides append-only audit trail logging, hash chain integrity verification, and cross-tenant access enforcement.
"""

import threading
from typing import Any, cast
from src.domain.audit_v2 import AuditActionType, AuditRecordV2


class AuditGovernanceV2Service:
    def __init__(self, repository: Any = None) -> None:
        self.repository = repository
        # Map tenant_id -> list of AuditRecordV2 (for in-memory / testing fallback)
        self._audit_chains: dict[str, list[AuditRecordV2]] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def _get_lock(self, tenant_id: str) -> threading.Lock:
        with self._global_lock:
            if tenant_id not in self._locks:
                self._locks[tenant_id] = threading.Lock()
            return self._locks[tenant_id]

    def record_action(
        self,
        tenant_id: str,
        actor_id: str,
        action_type: AuditActionType,
        resource: str,
        details: dict[str, Any] | None = None,
    ) -> AuditRecordV2:
        with self._get_lock(tenant_id):
            if self.repository and hasattr(self.repository, "get_latest_audit_record"):
                latest = self.repository.get_latest_audit_record(tenant_id)
                prev_hash = latest.hash if latest else "GENESIS"
            else:
                chain = self._audit_chains.get(tenant_id)
                if chain is None and self.repository:
                    chain = self.repository.load_audit_chain(tenant_id)
                    self._audit_chains[tenant_id] = chain
                prev_hash = chain[-1].hash if chain else "GENESIS"

            record = AuditRecordV2(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action_type=action_type,
                resource=resource,
                details=details or {},
                prev_hash=prev_hash,
            )
            record.hash = record.compute_hash()

            if tenant_id in self._audit_chains:
                self._audit_chains[tenant_id].append(record)
            else:
                self._audit_chains[tenant_id] = [record]

            if self.repository:
                self.repository.save_audit_record(record)

            return record

    def _chain(self, tenant_id: str) -> list[AuditRecordV2]:
        """The tenant's chain, loaded from storage the first time it is needed."""
        with self._get_lock(tenant_id):
            if self.repository:
                return cast(list[AuditRecordV2], self.repository.load_audit_chain(tenant_id))
            if tenant_id not in self._audit_chains:
                self._audit_chains[tenant_id] = []
            return self._audit_chains[tenant_id]

    def verify_audit_chain(self, tenant_id: str) -> bool:
        """
        Cryptographically verifies the hash chain for a tenant.
        Returns True if intact, False if tampered.
        """
        with self._get_lock(tenant_id):
            chain = (
                self.repository.load_audit_chain(tenant_id)
                if self.repository
                else self._audit_chains.get(tenant_id, [])
            )
            if not chain:
                return True

            expected_prev_hash = "GENESIS"
            for record in chain:
                if record.prev_hash != expected_prev_hash:
                    return False
                if record.hash != record.compute_hash():
                    return False
                expected_prev_hash = record.hash

            return True

    def get_audit_trail(self, tenant_id: str) -> list[AuditRecordV2]:
        return self._chain(tenant_id)

    def enforce_tenant_security(self, request_tenant_id: str, resource_tenant_id: str, actor_id: str = "system") -> None:
        """
        Enforces strict multi-tenant boundary. Raises PermissionError on mismatch and logs breach attempt.
        """
        if request_tenant_id != resource_tenant_id:
            self.record_action(
                tenant_id=request_tenant_id,
                actor_id=actor_id,
                action_type=AuditActionType.POLICY_VIOLATION,
                resource=f"CrossTenantAccess:{resource_tenant_id}",
                details={"attempted_target": resource_tenant_id},
            )
            raise PermissionError(f"Cross-tenant breach attempt blocked: {request_tenant_id} cannot access resource of {resource_tenant_id}")
