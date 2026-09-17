"""
Application engine for Data Integrity, SHA-256 Hash Chaining, & Audit Logging (Phase 30).
"""

import hashlib
import json
import logging
from datetime import datetime, timezone, UTC
from typing import Any, Dict, List, Optional, Tuple

from src.domain.exceptions import DisasterRecoveryError
from src.domain.repository import ResilienceRepositoryInterface
from src.domain.resilience import AuditTrailLog

logger = logging.getLogger(__name__)


class DataIntegrityEngine:
    """Engine enforcing immutable audit trail integrity, SHA-256 hash chaining, and state mutation verification."""

    def __init__(self, repository: ResilienceRepositoryInterface) -> None:
        self.repository = repository

    def compute_checksum(self, payload: Any) -> str:
        if isinstance(payload, str):
            data_bytes = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            data_bytes = payload
        else:
            data_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(data_bytes).hexdigest()

    async def log_mutation(
        self,
        actor_id: str,
        action: str,
        resource: str,
        previous_state: Optional[Any] = None,
        new_state: Optional[Any] = None,
        actor_type: str = "AGENT",
        enterprise_id: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> AuditTrailLog:
        prev_str = json.dumps(previous_state, sort_keys=True) if previous_state is not None else None
        new_str = json.dumps(new_state, sort_keys=True) if new_state is not None else None

        latest_log = await self.repository.get_latest_audit_log()
        prev_checksum = latest_log.checksum if latest_log else "GENESIS"

        raw_payload = f"{prev_checksum}:{actor_id}:{action}:{resource}:{prev_str}:{new_str}"
        checksum = self.compute_checksum(raw_payload)

        audit_entry = AuditTrailLog(
            actor_id=actor_id,
            actor_type=actor_type,
            enterprise_id=enterprise_id,
            company_id=company_id,
            action=action,
            resource=resource,
            previous_state=prev_str,
            new_state=new_str,
            checksum=checksum,
        )

        return await self.repository.save_audit_log(audit_entry)

    async def verify_audit_chain(self, limit: int = 100) -> Tuple[bool, List[str]]:
        logs = await self.repository.list_audit_logs(limit=limit)
        if not logs:
            return True, []

        logs = sorted(logs, key=lambda l: l.timestamp)
        errors = []
        expected_prev_checksum = "GENESIS"

        for i, log in enumerate(logs):
            if i == 0:
                expected_prev_checksum = log.checksum
                continue

            raw_payload = f"{logs[i-1].checksum}:{log.actor_id}:{log.action}:{log.resource}:{log.previous_state}:{log.new_state}"
            computed = self.compute_checksum(raw_payload)
            if computed != log.checksum:
                errors.append(f"Hash mismatch at log entry '{log.id}': recorded {log.checksum}, computed {computed}")

        is_valid = len(errors) == 0
        return is_valid, errors
