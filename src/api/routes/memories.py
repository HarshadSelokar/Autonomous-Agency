"""
FastAPI Routes for Phase 7 Memory Management.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.memory_schemas import (
    ConfirmMemoryRequest,
    CreateMemoryRequest,
    MemoryResponse,
    PromoteMemoryRequest,
)
from src.application.memory_retrieval_service import MemoryRetrievalService
from src.application.memory_service import MemoryService, UnauthorizedMemoryPromotionError
from src.domain.exceptions import EmployeeNotFoundError, ObjectiveValidationError
from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryProvenance,
    MemoryScope,
    MemoryType,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.memory_repository import SQLAlchemyMemoryRepository

router = APIRouter(prefix="/memories", tags=["Memories"])


def _to_memory_response(memory: MemoryEntry) -> MemoryResponse:
    return MemoryResponse(
        id=memory.id,
        memory_type=memory.memory_type.value,
        scope=memory.scope.value,
        owner_id=memory.owner_id,
        content=memory.content,
        summary=memory.summary,
        authority=memory.authority.value,
        confidence=memory.confidence,
        provenance=memory.provenance.value,
        status=memory.status.value,
        task_id=memory.task_id,
        decision_id=memory.decision_id,
        artifact_id=memory.artifact_id,
        created_at=memory.created_at,
    )


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: CreateMemoryRequest,
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    mem_repo = SQLAlchemyMemoryRepository(db)
    emp_repo = SQLAlchemyEmployeeRepository(db)
    service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)

    try:
        type_enum = MemoryType(payload.memory_type.upper())
        scope_enum = MemoryScope(payload.scope.upper())
        authority_enum = MemoryAuthority(payload.authority.upper())
        provenance_enum = MemoryProvenance(payload.provenance.upper())

        entry = await service.create_memory(
            memory_type=type_enum,
            scope=scope_enum,
            owner_id=payload.owner_id,
            content=payload.content,
            summary=payload.summary,
            authority=authority_enum,
            confidence=payload.confidence,
            provenance=provenance_enum,
            source_id=payload.source_id,
            task_id=payload.task_id,
            employee_id=payload.employee_id,
            agent_run_id=payload.agent_run_id,
            meeting_id=payload.meeting_id,
            decision_id=payload.decision_id,
            artifact_id=payload.artifact_id,
        )
        await db.commit()
        return _to_memory_response(entry)
    except (UnauthorizedMemoryPromotionError, ObjectiveValidationError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    owner_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[MemoryResponse]:
    repo = SQLAlchemyMemoryRepository(db)
    if owner_id:
        entries = await repo.list_by_owner(owner_id)
    else:
        entries = await repo.list_all()
    return [_to_memory_response(m) for m in entries]


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    repo = SQLAlchemyMemoryRepository(db)
    entry = await repo.get_by_id(memory_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found.")
    return _to_memory_response(entry)


@router.post("/{memory_id}/confirm", response_model=MemoryResponse)
async def confirm_memory(
    memory_id: str,
    payload: ConfirmMemoryRequest,
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    mem_repo = SQLAlchemyMemoryRepository(db)
    emp_repo = SQLAlchemyEmployeeRepository(db)
    service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)

    try:
        confirmed = await service.confirm_memory(memory_id=memory_id, actor_employee_id=payload.actor_employee_id)
        await db.commit()
        return _to_memory_response(confirmed)
    except EmployeeNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{memory_id}/promote", response_model=MemoryResponse)
async def promote_memory(
    memory_id: str,
    payload: PromoteMemoryRequest,
    db: AsyncSession = Depends(get_db),
) -> MemoryResponse:
    mem_repo = SQLAlchemyMemoryRepository(db)
    emp_repo = SQLAlchemyEmployeeRepository(db)
    service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)

    try:
        target_auth = MemoryAuthority(payload.target_authority.upper())
        promoted = await service.promote_memory(
            memory_id=memory_id, target_authority=target_auth, actor_employee_id=payload.actor_employee_id
        )
        await db.commit()
        return _to_memory_response(promoted)
    except UnauthorizedMemoryPromotionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except EmployeeNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
