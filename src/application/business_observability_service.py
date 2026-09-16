"""
Business Observability & Telemetry Service for Phase 23.

Provides structured logging, financial audit records, and telemetry for business operations.
Sensitive credentials and financial accounts are redacted in telemetry logs.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("business_observability")


class BusinessObservabilityService:
    """Logs financial audit events and metrics while enforcing secret/PII redaction."""

    def __init__(self) -> None:
        self._audit_log: List[Dict[str, Any]] = []

    def _redact_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts sensitive banking identifiers, API tokens, and secret fields."""
        sensitive_keys = {"bank_account", "api_key", "secret", "token", "password", "card_number"}
        redacted = {}
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                redacted[k] = "[REDACTED]"
            elif isinstance(v, dict):
                redacted[k] = self._redact_sensitive(v)
            else:
                redacted[k] = v
        return redacted

    def log_financial_action(
        self,
        action: str,
        actor_id: str,
        amount_cents: int,
        currency: str = "USD",
        status: str = "SUCCESS",
        evidence_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        safe_meta = self._redact_sensitive(metadata or {})
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "actor_id": actor_id,
            "amount_cents": amount_cents,
            "currency": currency,
            "status": status,
            "evidence_reference": evidence_reference,
            "metadata": safe_meta,
        }
        self._audit_log.append(record)
        logger.info(f"[FINANCIAL AUDIT] {action} by {actor_id} | Amount: {amount_cents} {currency} | Status: {status}")
        return record

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        return list(self._audit_log)
