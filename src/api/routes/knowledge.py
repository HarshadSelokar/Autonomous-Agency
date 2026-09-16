"""FastAPI Routes for Phase 18 Institutional Knowledge & Memory Services."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.knowledge import (
    CreateKnowledgeItemRequest,
    CreateProcedureRequest,
    KnowledgeConflictResponse,
    KnowledgeItemResponse,
    KnowledgeValidationResponse,
    ProcedureResponse,
    ResolveConflictRequest,
    ValidateKnowledgeRequest,
)
from src.application.knowledge_validation_service import KnowledgeValidationService
from src.application.procedure_management_service import ProcedureManagementService
from src.domain.knowledge import (
    KnowledgeAuthority,
    KnowledgeItem,
    KnowledgeProvenance,
    KnowledgeScope,
    KnowledgeStatus,
    KnowledgeType,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository

router = APIRouter(prefix="/knowledge", tags=["Institutional Knowledge"])


def _to_item_response(item: KnowledgeItem) -> KnowledgeItemResponse:
    return KnowledgeItemResponse(
        id=item.id,
        statement=item.statement,
        knowledge_type=item.knowledge_type.value if hasattr(item.knowledge_type, "value") else str(item.knowledge_type),
        scope=item.scope.value if hasattr(item.scope, "value") else str(item.scope),
        authority=item.authority.value if hasattr(item.authority, "value") else str(item.authority),
        status=item.status.value if hasattr(item.status, "value") else str(item.status),
        confidence=item.confidence,
        created_at=item.created_at,
    )


@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_item(
    payload: CreateKnowledgeItemRequest,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeItemResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    item = KnowledgeItem(
        statement=payload.statement,
        knowledge_type=KnowledgeType(payload.knowledge_type.upper()),
        scope=KnowledgeScope(payload.scope.upper()),
        confidence=payload.confidence,
        status=KnowledgeStatus.CANDIDATE,
        authority=KnowledgeAuthority.UNVERIFIED,
    )
    saved = await repo.save_knowledge_item(item)
    await db.commit()
    return _to_item_response(saved)


@router.get("", response_model=list[KnowledgeItemResponse])
async def list_knowledge_items(
    scope: str | None = None,
    authority: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeItemResponse]:
    repo = SQLAlchemyKnowledgeRepository(db)
    scope_enum = KnowledgeScope(scope.upper()) if scope else None
    auth_enum = KnowledgeAuthority(authority.upper()) if authority else None
    status_enum = KnowledgeStatus(status_filter.upper()) if status_filter else None

    items = await repo.list_knowledge_items(scope=scope_enum, authority=auth_enum, status=status_enum)
    return [_to_item_response(it) for it in items]


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeItemResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    item = await repo.get_knowledge_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Knowledge item '{item_id}' not found.")
    return _to_item_response(item)


@router.post("/{item_id}/validate", response_model=KnowledgeValidationResponse)
async def validate_knowledge_item(
    item_id: str,
    payload: ValidateKnowledgeRequest,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeValidationResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    val_svc = KnowledgeValidationService(repo)

    val_record = await val_svc.validate_candidate_knowledge(
        knowledge_id=item_id,
        validator_id=payload.validator_id,
        evidence_ids=payload.evidence_ids,
        rationale=payload.rationale,
    )
    await db.commit()
    return KnowledgeValidationResponse(
        id=val_record.id,
        knowledge_id=val_record.knowledge_id,
        validator_id=val_record.validator_id,
        validation_status=val_record.validation_status,
        rationale=val_record.rationale,
        evidence_ids=val_record.evidence_ids,
        created_at=val_record.timestamp if hasattr(val_record, "timestamp") else val_record.created_at,
    )


@router.get("/{item_id}/conflicts", response_model=list[KnowledgeConflictResponse])
async def check_item_conflicts(
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeConflictResponse]:
    repo = SQLAlchemyKnowledgeRepository(db)
    val_svc = KnowledgeValidationService(repo)
    item = await repo.get_knowledge_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Knowledge item '{item_id}' not found.")

    conflicts = await val_svc.detect_conflicts_for_item(item)
    return [
        KnowledgeConflictResponse(
            id=c.id,
            knowledge_id_a=c.knowledge_id_a,
            knowledge_id_b=c.knowledge_id_b,
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
            resolution_strategy=c.resolution_strategy,
            winning_knowledge_id=c.winning_knowledge_id if hasattr(c, "winning_knowledge_id") else None,
            created_at=c.created_at,
        )
        for c in conflicts
    ]


@router.post("/conflicts/{conflict_id}/resolve", response_model=KnowledgeConflictResponse)
async def resolve_conflict(
    conflict_id: str,
    payload: ResolveConflictRequest,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeConflictResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    val_svc = KnowledgeValidationService(repo)

    try:
        resolved = await val_svc.resolve_conflict(
            conflict_id=conflict_id,
            resolution_strategy=payload.resolution_strategy,
            winning_knowledge_id=payload.winning_knowledge_id,
        )
        await db.commit()
        return KnowledgeConflictResponse(
            id=resolved.id,
            knowledge_id_a=resolved.knowledge_id_a,
            knowledge_id_b=resolved.knowledge_id_b,
            status=resolved.status.value if hasattr(resolved.status, "value") else str(resolved.status),
            resolution_strategy=resolved.resolution_strategy,
            winning_knowledge_id=payload.winning_knowledge_id,
            created_at=resolved.created_at,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/procedures", response_model=ProcedureResponse, status_code=status.HTTP_201_CREATED)
async def create_procedure(
    payload: CreateProcedureRequest,
    db: AsyncSession = Depends(get_db),
) -> ProcedureResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    proc_svc = ProcedureManagementService(repo)

    scope_enum = KnowledgeScope(payload.scope.upper())
    proc = await proc_svc.create_procedure(
        title=payload.title,
        purpose=payload.purpose,
        steps=payload.steps,
        expected_outcome=payload.expected_outcome,
        prerequisites=payload.prerequisites,
        verification_criteria=payload.verification_criteria,
        scope=scope_enum,
    )
    await db.commit()
    return ProcedureResponse(
        id=proc.id,
        title=proc.title,
        purpose=proc.purpose,
        version=proc.version,
        steps=proc.steps,
        expected_outcome=proc.expected_outcome,
        is_governance_approved=proc.is_governance_approved,
        validation_status=proc.validation_status.value if hasattr(proc.validation_status, "value") else str(proc.validation_status),
        created_at=proc.created_at,
    )


@router.post("/procedures/{proc_id}/approve", response_model=ProcedureResponse)
async def approve_procedure(
    proc_id: str,
    governance_approval_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProcedureResponse:
    repo = SQLAlchemyKnowledgeRepository(db)
    proc_svc = ProcedureManagementService(repo)

    try:
        proc = await proc_svc.approve_procedure_by_governance(proc_id, governance_approval_id)
        await db.commit()
        return ProcedureResponse(
            id=proc.id,
            title=proc.title,
            purpose=proc.purpose,
            version=proc.version,
            steps=proc.steps,
            expected_outcome=proc.expected_outcome,
            is_governance_approved=proc.is_governance_approved,
            validation_status=proc.validation_status.value if hasattr(proc.validation_status, "value") else str(proc.validation_status),
            created_at=proc.created_at,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
