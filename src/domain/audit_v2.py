"""
Domain models for Security, Governance & Audit 2.0 (Phase 40).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import hashlib
import json
import uuid


class AuditActionType(str, Enum):
    TENANT_ACCESS = "TENANT_ACCESS"
    USER_AUTH = "USER_AUTH"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
    WORKFLOW_EXECUTION = "WORKFLOW_EXECUTION"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    POLICY_VIOLATION = "POLICY_VIOLATION"


@dataclass
class AuditRecordV2:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    actor_id: str = ""
    action_type: AuditActionType = AuditActionType.TENANT_ACCESS
    resource: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    prev_hash: str = ""
    hash: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def compute_hash(self) -> str:
        content = f"{self.id}:{self.tenant_id}:{self.actor_id}:{self.action_type.value}:{self.resource}:{json.dumps(self.details, sort_keys=True)}:{self.prev_hash}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
