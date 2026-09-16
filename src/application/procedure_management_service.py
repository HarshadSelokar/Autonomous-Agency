"""
ProcedureManagementService for Phase 18.

Manages versioned organizational procedures, learned procedures from recurring patterns,
and Phase 11 Governance authorization integration.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from src.domain.events import (
    DomainEvent,
    KnowledgeProcedureApprovedEvent,
    KnowledgeProcedureProposedEvent,
)
from src.domain.knowledge import KnowledgeProcedure, KnowledgeScope, KnowledgeStatus
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository


class ProcedureManagementService:
    def __init__(
        self,
        repository: SQLAlchemyKnowledgeRepository,
        governance_service: Any | None = None,
        outbox_publisher: Any | None = None,
    ) -> None:
        self.repo = repository
        self.governance_svc = governance_service
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_procedure(
        self,
        title: str,
        purpose: str,
        steps: list[dict[str, Any]],
        expected_outcome: str,
        prerequisites: list[str] | None = None,
        verification_criteria: list[str] | None = None,
        failure_conditions: list[str] | None = None,
        rollback_steps: list[str] | None = None,
        scope: KnowledgeScope = KnowledgeScope.COMPANY,
        owner_id: str = "system",
    ) -> KnowledgeProcedure:
        """Create a new versioned procedure candidate."""
        proc = KnowledgeProcedure(
            id=f"proc-{uuid.uuid4().hex[:8]}",
            title=title,
            purpose=purpose,
            prerequisites=prerequisites or [],
            steps=steps,
            expected_outcome=expected_outcome,
            verification_criteria=verification_criteria or [],
            failure_conditions=failure_conditions or [],
            rollback_steps=rollback_steps or [],
            scope=scope,
            owner_id=owner_id,
            version=1,
            validation_status=KnowledgeStatus.CANDIDATE,
            is_governance_approved=False,
            created_at=datetime.now(UTC),
        )

        saved = await self.repo.save_procedure(proc)

        self._publish_event(
            KnowledgeProcedureProposedEvent(
                procedure_id=saved.id,
                title=saved.title,
                version=saved.version,
            )
        )

        return saved

    async def propose_procedure_from_pattern(
        self,
        pattern_id: str,
        title: str,
        purpose: str,
        steps: list[dict[str, Any]],
        expected_outcome: str,
    ) -> KnowledgeProcedure:
        """
        Convert a recurring validated pattern into a procedure candidate.
        CRITICAL INVARIANT: Learned procedures are candidates and DO NOT automatically become binding policy.
        """
        return await self.create_procedure(
            title=title,
            purpose=purpose,
            steps=steps,
            expected_outcome=expected_outcome,
            owner_id=f"pattern_learning:{pattern_id}",
        )

    async def approve_procedure_by_governance(
        self,
        procedure_id: str,
        governance_approval_id: str,
    ) -> KnowledgeProcedure:
        """Approve procedure candidate by Phase 11 Human Governance."""
        proc = await self.repo.get_procedure_by_id(procedure_id)
        if not proc:
            raise ValueError(f"Procedure {procedure_id} not found")

        proc.is_governance_approved = True
        proc.validation_status = KnowledgeStatus.AUTHORITATIVE
        saved = await self.repo.save_procedure(proc)

        self._publish_event(
            KnowledgeProcedureApprovedEvent(
                procedure_id=saved.id,
                governance_approval_id=governance_approval_id,
            )
        )

        return saved
