"""
FastAPI Routes for Phase 7 Artifact Management.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.artifact_schemas import ArtifactResponse, CreateArtifactRequest
from src.domain.artifact import Artifact, compute_sha256
from src.infrastructure.database import get_db
from src.infrastructure.repositories.artifact_repository import SQLAlchemyArtifactRepository
from src.infrastructure.repositories.workspace_repository import SQLAlchemyWorkspaceRepository
from src.infrastructure.storage_provider import LocalStorageProvider

router = APIRouter(tags=["Artifacts"])


def _to_artifact_response(artifact: Artifact) -> ArtifactResponse:
    return ArtifactResponse(
        id=artifact.id,
        workspace_id=artifact.workspace_id,
        name=artifact.name,
        mime_type=artifact.mime_type,
        size_bytes=artifact.size_bytes,
        checksum_sha256=artifact.checksum_sha256,
        version=artifact.version,
        created_by_employee_id=artifact.created_by_employee_id,
        status=artifact.status.value,
        created_at=artifact.created_at,
    )


@router.post("/workspaces/{workspace_id}/artifacts", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    workspace_id: str,
    payload: CreateArtifactRequest,
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    ws_repo = SQLAlchemyWorkspaceRepository(db)
    ws = await ws_repo.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found.")

    storage = LocalStorageProvider()
    content_bytes = payload.content_base64_or_text.encode("utf-8")
    checksum = compute_sha256(content_bytes)

    art_id = f"art-{uuid.uuid4().hex[:8]}"
    storage_key = f"workspaces/{workspace_id}/{art_id}/v1_{payload.name}"
    await storage.store_bytes(storage_key, content_bytes)

    art = Artifact(
        id=art_id,
        workspace_id=workspace_id,
        name=payload.name,
        mime_type=payload.mime_type,
        size_bytes=len(content_bytes),
        checksum_sha256=checksum,
        created_by_employee_id=payload.created_by_employee_id,
        version=1,
        source_run_id=payload.source_run_id,
        task_id=payload.task_id,
        storage_key=storage_key,
    )

    art_repo = SQLAlchemyArtifactRepository(db)
    saved = await art_repo.save(art)
    await db.commit()
    return _to_artifact_response(saved)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    art_repo = SQLAlchemyArtifactRepository(db)
    art = await art_repo.get_by_id(artifact_id)
    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{artifact_id}' not found.")
    return _to_artifact_response(art)


@router.get("/workspaces/{workspace_id}/artifacts", response_model=list[ArtifactResponse])
async def list_workspace_artifacts(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactResponse]:
    art_repo = SQLAlchemyArtifactRepository(db)
    artifacts = await art_repo.list_by_workspace_id(workspace_id)
    return [_to_artifact_response(a) for a in artifacts]


@router.post("/artifacts/{artifact_id}/versions", response_model=ArtifactResponse)
async def create_artifact_version(
    artifact_id: str,
    payload: CreateArtifactRequest,
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    art_repo = SQLAlchemyArtifactRepository(db)
    parent_art = await art_repo.get_by_id(artifact_id)
    if not parent_art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{artifact_id}' not found.")

    storage = LocalStorageProvider()
    content_bytes = payload.content_base64_or_text.encode("utf-8")
    checksum = compute_sha256(content_bytes)

    new_version_art_id = f"art-{uuid.uuid4().hex[:8]}"
    storage_key = f"workspaces/{parent_art.workspace_id}/{new_version_art_id}/v{parent_art.version + 1}_{payload.name}"
    await storage.store_bytes(storage_key, content_bytes)

    new_version_art = parent_art.create_next_version(
        new_artifact_id=new_version_art_id,
        size_bytes=len(content_bytes),
        checksum_sha256=checksum,
        storage_key=storage_key,
        creator_employee_id=payload.created_by_employee_id,
        source_run_id=payload.source_run_id,
    )
    # Save both parent (now SUPERSEDED) and new version (ACTIVE)
    await art_repo.save(parent_art)
    saved = await art_repo.save(new_version_art)
    await db.commit()
    return _to_artifact_response(saved)
