"""
FastAPI Routes for Phase 7 Workspace Management.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.workspace_schemas import CreateWorkspaceRequest, WorkspaceResponse
from src.domain.workspace import Workspace, WorkspaceStatus, WorkspaceType
from src.infrastructure.database import get_db
from src.infrastructure.repositories.workspace_repository import SQLAlchemyWorkspaceRepository

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


def _to_workspace_response(workspace: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        workspace_type=workspace.workspace_type.value,
        owner_id=workspace.owner_id,
        status=workspace.status.value,
        task_id=workspace.task_id,
        project_id=workspace.project_id,
        employee_id=workspace.employee_id,
        created_at=workspace.created_at,
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: CreateWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    repo = SQLAlchemyWorkspaceRepository(db)
    type_enum = WorkspaceType(payload.workspace_type.upper())
    ws_id = f"ws-{uuid.uuid4().hex[:8]}"
    ws = Workspace(
        id=ws_id,
        name=payload.name,
        workspace_type=type_enum,
        owner_id=payload.owner_id,
        status=WorkspaceStatus.ACTIVE,
        task_id=payload.task_id,
        project_id=payload.project_id,
        employee_id=payload.employee_id,
    )
    saved = await repo.save(ws)
    await db.commit()
    return _to_workspace_response(saved)


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    owner_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceResponse]:
    repo = SQLAlchemyWorkspaceRepository(db)
    if owner_id:
        workspaces = await repo.list_by_owner(owner_id)
    else:
        workspaces = await repo.list_all()
    return [_to_workspace_response(w) for w in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    repo = SQLAlchemyWorkspaceRepository(db)
    ws = await repo.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found.")
    return _to_workspace_response(ws)


@router.post("/{workspace_id}/lock", response_model=WorkspaceResponse)
async def lock_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    repo = SQLAlchemyWorkspaceRepository(db)
    ws = await repo.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found.")
    ws.lock()
    saved = await repo.save(ws)
    await db.commit()
    return _to_workspace_response(saved)


@router.post("/{workspace_id}/archive", response_model=WorkspaceResponse)
async def archive_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    repo = SQLAlchemyWorkspaceRepository(db)
    ws = await repo.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found.")
    ws.archive()
    saved = await repo.save(ws)
    await db.commit()
    return _to_workspace_response(saved)
