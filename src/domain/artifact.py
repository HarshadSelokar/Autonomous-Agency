"""
Artifact Domain Entity, Versioning, and Lifecycle State Machine for Phase 7.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class ArtifactStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class ArtifactValidationError(ObjectiveValidationError):
    """Raised when artifact domain constraints or checksum validations fail."""

    pass


@dataclass
class Artifact:
    id: str
    workspace_id: str
    name: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    created_by_employee_id: str
    version: int = 1
    source_run_id: str | None = None
    task_id: str | None = None
    status: ArtifactStatus = ArtifactStatus.ACTIVE
    storage_key: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ArtifactValidationError("Artifact ID cannot be empty.")
        if not self.workspace_id or not self.workspace_id.strip():
            raise ArtifactValidationError("Artifact workspace_id cannot be empty.")
        if not self.name or not self.name.strip():
            raise ArtifactValidationError("Artifact name cannot be empty.")
        if not self.created_by_employee_id or not self.created_by_employee_id.strip():
            raise ArtifactValidationError("Artifact created_by_employee_id cannot be empty.")
        if self.version < 1:
            raise ArtifactValidationError("Artifact version must be >= 1.")

    def create_next_version(
        self,
        new_artifact_id: str,
        size_bytes: int,
        checksum_sha256: str,
        storage_key: str,
        creator_employee_id: str,
        source_run_id: str | None = None,
    ) -> "Artifact":
        """Produce next version of the artifact while preserving current version as SUPERSEDED."""
        self.status = ArtifactStatus.SUPERSEDED
        self.updated_at = datetime.now(UTC)

        return Artifact(
            id=new_artifact_id,
            workspace_id=self.workspace_id,
            name=self.name,
            mime_type=self.mime_type,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            created_by_employee_id=creator_employee_id,
            version=self.version + 1,
            source_run_id=source_run_id or self.source_run_id,
            task_id=self.task_id,
            status=ArtifactStatus.ACTIVE,
            storage_key=storage_key,
            metadata=dict(self.metadata),
        )


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()
