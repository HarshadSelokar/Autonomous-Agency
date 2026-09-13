"""
SQLAlchemy ORM Model for Artifact persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.artifact import Artifact, ArtifactStatus
from src.infrastructure.database import Base


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_employee_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_run_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    task_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="ACTIVE", index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def artifact_model_to_domain(model: ArtifactModel) -> Artifact:
    return Artifact(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        mime_type=model.mime_type,
        size_bytes=model.size_bytes,
        checksum_sha256=model.checksum_sha256,
        created_by_employee_id=model.created_by_employee_id,
        version=model.version,
        source_run_id=model.source_run_id,
        task_id=model.task_id,
        status=ArtifactStatus(model.status),
        storage_key=model.storage_key,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def artifact_domain_to_model(domain: Artifact) -> ArtifactModel:
    return ArtifactModel(
        id=domain.id,
        workspace_id=domain.workspace_id,
        name=domain.name,
        mime_type=domain.mime_type,
        size_bytes=domain.size_bytes,
        checksum_sha256=domain.checksum_sha256,
        created_by_employee_id=domain.created_by_employee_id,
        version=domain.version,
        source_run_id=domain.source_run_id,
        task_id=domain.task_id,
        status=domain.status.value,
        storage_key=domain.storage_key,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
