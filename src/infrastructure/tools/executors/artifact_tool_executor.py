"""
Artifact Tool Executor Adapter for Phase 8.
Handles READ_ARTIFACT, CREATE_ARTIFACT, and UPDATE_ARTIFACT integrating with Phase 7 Artifact domain & storage.
"""

import time
from typing import Any

from src.application.secrets_broker import SecretsBroker
from src.domain.artifact import Artifact, compute_sha256
from src.domain.tool import (
    ToolCapability,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from src.infrastructure.repositories.artifact_repository import SQLAlchemyArtifactRepository
from src.infrastructure.storage_provider import LocalStorageProvider, StorageProviderInterface
from src.infrastructure.tools.executors.base import ToolExecutorInterface


class ArtifactToolExecutor(ToolExecutorInterface):
    def __init__(
        self,
        artifact_repo: SQLAlchemyArtifactRepository | None = None,
        storage_provider: StorageProviderInterface | None = None,
    ) -> None:
        self.artifact_repo = artifact_repo
        self.storage_provider = storage_provider or LocalStorageProvider()

    async def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
        secrets_broker: SecretsBroker | None = None,
    ) -> ToolResult:
        start_time = time.time()
        cap = request.requested_capability
        args = request.arguments

        try:
            if cap == ToolCapability.READ_ARTIFACT:
                artifact_id = args.get("artifact_id")
                if not artifact_id:
                    raise ValueError("Argument 'artifact_id' is required for READ_ARTIFACT capability.")

                if self.artifact_repo:
                    art = await self.artifact_repo.get_by_id(artifact_id)
                    if not art:
                        raise FileNotFoundError(f"Artifact '{artifact_id}' not found.")
                    storage_key = art.storage_key
                    name = art.name
                    version = art.version
                else:
                    storage_key = args.get("storage_key", artifact_id)
                    name = args.get("name", "artifact")
                    version = 1

                content_bytes = await self.storage_provider.read_bytes(storage_key)
                content_str = content_bytes.decode("utf-8", errors="ignore")
                elapsed = (time.time() - start_time) * 1000

                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={
                        "artifact_id": artifact_id,
                        "name": name,
                        "version": version,
                        "content": content_str,
                        "size_bytes": len(content_bytes),
                    },
                    execution_time_ms=elapsed,
                )

            elif cap in {ToolCapability.CREATE_ARTIFACT, ToolCapability.UPDATE_ARTIFACT}:
                name = args.get("name") or "output_artifact.md"
                content_str = args.get("content", "")
                mime_type = args.get("mime_type", "text/markdown")
                workspace_id = request.workspace_id or "default-workspace"

                content_bytes = content_str.encode("utf-8")
                checksum = compute_sha256(content_bytes)

                art_id = args.get("artifact_id") or f"art-{request.id[:8]}"
                storage_key = f"workspaces/{workspace_id}/{art_id}_{name}"

                await self.storage_provider.store_bytes(storage_key, content_bytes)
                elapsed = (time.time() - start_time) * 1000

                return ToolResult(
                    execution_id=request.id,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output={
                        "artifact_id": art_id,
                        "workspace_id": workspace_id,
                        "name": name,
                        "checksum_sha256": checksum,
                        "size_bytes": len(content_bytes),
                        "storage_key": storage_key,
                        "created_by_employee_id": request.employee_id,
                    },
                    evidence_id=f"evid-{art_id}",
                    execution_time_ms=elapsed,
                )

            else:
                raise ValueError(f"ArtifactToolExecutor does not support capability '{cap.value}'.")

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.FAILED,
                error_message=str(exc),
                execution_time_ms=elapsed,
            )
