"""
Application engine for Security Incident Management, Adversarial Filtering, & Secret Redaction (Phase 30).
"""

import logging
import re
from datetime import datetime, timezone, UTC
from typing import Any, Dict, List, Optional, Tuple

from src.domain.exceptions import SecurityBoundaryViolationError
from src.domain.repository import ResilienceRepositoryInterface
from src.domain.resilience import (
    SecurityIncident,
    SecurityIncidentStatus,
    SecuritySeverity,
    SecuritySignal,
)

logger = logging.getLogger(__name__)


PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directions|prompts|guidelines)",
    r"(?i)bypass\s+(security|safety|governance|guardrails|policies)",
    r"(?i)system\s*:\s*you\s+are\s+now\s+an\s+unrestricted",
    r"(?i)reveal\s+(system\s+prompt|secret\s+keys|auth\s+tokens|passwords)",
    r"(?i)override\s+governance\s+approval",
    r"(?i)jailbreak",
]

SECRET_REDACTION_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{24,}", "[REDACTED_API_KEY]"),
    (r"ghp_[a-zA-Z0-9]{36}", "[REDACTED_GITHUB_TOKEN]"),
    (r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "[REDACTED_JWT_TOKEN]"),
    (r"(?i)(password|secret|api_key|auth_token)\s*[:=]\s*['\"]?[^'\";\s]{8,}['\"]?", r"\1: [REDACTED_SECRET]"),
    (r"postgres://[a-zA-Z0-9_]+:[^@]+@", "postgres://[REDACTED_CREDS]@"),
]


class SecurityIncidentEngine:
    """Engine handling adversarial filtering, secret redaction, and security incident management."""

    def __init__(self, repository: ResilienceRepositoryInterface) -> None:
        self.repository = repository

    def analyze_prompt_security(self, content: str, source: str = "user_input") -> Tuple[bool, SecuritySignal]:
        flagged_pattern = None
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, content):
                flagged_pattern = pattern
                break

        is_blocked = flagged_pattern is not None
        sanitized = self.redact_secrets(content)

        signal = SecuritySignal(
            source=source,
            signal_type="PROMPT_INJECTION_ATTEMPT" if is_blocked else "BENIGN_PROMPT",
            severity=SecuritySeverity.HIGH if is_blocked else SecuritySeverity.INFO,
            raw_content=content[:500],
            sanitized_content=sanitized[:500],
            is_blocked=is_blocked,
            metadata={"matched_pattern": flagged_pattern} if flagged_pattern else {},
        )

        return is_blocked, signal

    def redact_secrets(self, text: str) -> str:
        if not text:
            return ""

        redacted = text
        for pattern, replacement in SECRET_REDACTION_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted)

        return redacted

    async def inspect_and_guard(self, content: str, source: str = "api_gateway", actor_id: str = "external_user") -> str:
        is_blocked, signal = self.analyze_prompt_security(content, source=source)
        await self.repository.save_security_signal(signal)

        if is_blocked:
            incident = SecurityIncident(
                title=f"Adversarial Prompt Injection from {source}",
                description=f"Blocked prompt injection attempt matching pattern: {signal.metadata.get('matched_pattern')}",
                severity=SecuritySeverity.HIGH,
                status=SecurityIncidentStatus.DETECTED,
                affected_components=[source],
            )
            await self.repository.save_security_incident(incident)
            logger.warning(f"Security boundary violation detected from {source}")
            raise SecurityBoundaryViolationError(
                actor_id=actor_id,
                violation_type="PROMPT_INJECTION",
                details=f"Malicious prompt injection pattern detected in input from '{source}'",
            )

        return self.redact_secrets(content)

    async def raise_incident(
        self,
        title: str,
        description: str,
        severity: SecuritySeverity = SecuritySeverity.HIGH,
        affected_components: Optional[List[str]] = None,
    ) -> SecurityIncident:
        incident = SecurityIncident(
            title=title,
            description=description,
            severity=severity,
            status=SecurityIncidentStatus.DETECTED,
            affected_components=affected_components or [],
        )
        return await self.repository.save_security_incident(incident)

    async def triage_incident(self, incident_id: str, new_severity: Optional[SecuritySeverity] = None) -> SecurityIncident:
        incidents = await self.repository.list_security_incidents()
        target = next((i for i in incidents if i.id == incident_id), None)
        if not target:
            raise KeyError(f"Security incident '{incident_id}' not found")

        target.status = SecurityIncidentStatus.TRIAGED
        if new_severity:
            target.severity = new_severity

        return await self.repository.save_security_incident(target)

    async def contain_incident(self, incident_id: str, governance_approval_id: Optional[str] = None) -> SecurityIncident:
        incidents = await self.repository.list_security_incidents()
        target = next((i for i in incidents if i.id == incident_id), None)
        if not target:
            raise KeyError(f"Security incident '{incident_id}' not found")

        target.status = SecurityIncidentStatus.CONTAINED
        target.governance_approval_id = governance_approval_id
        return await self.repository.save_security_incident(target)

    async def resolve_incident(self, incident_id: str) -> SecurityIncident:
        incidents = await self.repository.list_security_incidents()
        target = next((i for i in incidents if i.id == incident_id), None)
        if not target:
            raise KeyError(f"Security incident '{incident_id}' not found")

        target.status = SecurityIncidentStatus.RESOLVED
        target.resolved_at = datetime.now(UTC)
        return await self.repository.save_security_incident(target)
