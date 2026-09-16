"""
KnowledgeValidationService for Phase 18 Institutional Knowledge.

Handles candidate validation pipeline, independent evidence validation,
conflict detection and resolution, knowledge decay, and authority promotion.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Sequence
import uuid

from src.domain.events import (
    DomainEvent,
    KnowledgeAuthorityPromotedEvent,
    KnowledgeConflictDetectedEvent,
    KnowledgeConflictResolvedEvent,
    KnowledgeMarkedStaleEvent,
    KnowledgeValidatedEvent,
)
from src.domain.knowledge import (
    ConflictStatus,
    KnowledgeAuthority,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeValidation,
)
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository


class KnowledgeValidationService:
    def __init__(
        self,
        repository: SQLAlchemyKnowledgeRepository,
        outbox_publisher: Any | None = None,
    ) -> None:
        self.repo = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    def validate_independent_evidence(self, evidence_ids: Sequence[str]) -> bool:
        """
        CRITICAL INVARIANT TEST:
        Multiple LLM outputs do NOT count as independent evidence.
        Evidence must come from deterministic verification logs, system telemetry, or artifacts.
        """
        if not evidence_ids:
            return False
        valid_count = 0
        for ev in evidence_ids:
            ev_lower = ev.lower() if ev else ""
            if ev_lower and not (ev_lower.startswith("llm") or "llm_gen" in ev_lower or "llm-gen" in ev_lower or "llm_generated" in ev_lower or "llm_text" in ev_lower):
                valid_count += 1
        return valid_count >= 1

    async def validate_candidate_knowledge(
        self,
        knowledge_id: str,
        validator_id: str,
        evidence_ids: list[str],
        validator_type: str = "DETERMINISTIC_VERIFICATION",
        rationale: str = "Evidence-backed validation",
    ) -> KnowledgeValidation:
        """
        Executes Candidate Validation Pipeline:
        Candidate -> Source Validation -> Evidence Validation -> Consistency -> Independent Evidence -> Validation -> Authority Update.
        """
        item = await self.repo.get_knowledge_item_by_id(knowledge_id)
        if not item:
            raise ValueError(f"Knowledge item {knowledge_id} not found")

        # Check for explicit failure indicators in evidence
        has_failure_evidence = any("fail" in ev.lower() or "error" in ev.lower() for ev in evidence_ids)
        if has_failure_evidence:
            item.status = KnowledgeStatus.INVALIDATED
            await self.repo.save_knowledge_item(item)
            val = KnowledgeValidation(
                id=f"val-{uuid.uuid4().hex[:8]}",
                knowledge_id=knowledge_id,
                validator_id=validator_id,
                validator_type=validator_type,
                evidence_ids=evidence_ids,
                validation_status="FAILED",
                confidence_delta=0.0,
                rationale=f"Validation failed due to negative evidence: {rationale}",
                timestamp=datetime.now(UTC),
            )
            return await self.repo.save_validation(val)

        # Independent evidence check
        has_valid_evidence = self.validate_independent_evidence(evidence_ids)
        if not has_valid_evidence:
            val = KnowledgeValidation(
                id=f"val-{uuid.uuid4().hex[:8]}",
                knowledge_id=knowledge_id,
                validator_id=validator_id,
                validator_type=validator_type,
                evidence_ids=evidence_ids,
                validation_status="FAILED",
                confidence_delta=0.0,
                rationale="Validation failed: Insufficient or non-independent evidence (LLM outputs alone do not count as independent evidence).",
                timestamp=datetime.now(UTC),
            )
            return await self.repo.save_validation(val)

        # Check for conflicts
        conflicts = await self.detect_conflicts_for_item(item)

        validation_status = "PASSED" if not conflicts else "INCONCLUSIVE"
        confidence_delta = +0.3 if not conflicts else 0.0

        val = KnowledgeValidation(
            id=f"val-{uuid.uuid4().hex[:8]}",
            knowledge_id=knowledge_id,
            validator_id=validator_id,
            validator_type=validator_type,
            evidence_ids=evidence_ids,
            validation_status=validation_status,
            confidence_delta=confidence_delta,
            rationale=rationale,
            timestamp=datetime.now(UTC),
        )

        saved_val = await self.repo.save_validation(val)

        if validation_status == "PASSED":
            old_auth = item.authority.value
            item.confidence = min(1.0, item.confidence + confidence_delta)
            item.promote_authority(KnowledgeAuthority.VALIDATED)
            await self.repo.save_knowledge_item(item)

            self._publish_event(
                KnowledgeValidatedEvent(
                    knowledge_id=knowledge_id,
                    validator_id=validator_id,
                    validation_status="PASSED",
                )
            )
            self._publish_event(
                KnowledgeAuthorityPromotedEvent(
                    knowledge_id=knowledge_id,
                    old_authority=old_auth,
                    new_authority=item.authority.value,
                )
            )

        return saved_val

    async def detect_conflicts_for_item(self, item: KnowledgeItem) -> list[KnowledgeConflict]:
        """Detect potential contradictory statements with active knowledge items."""
        existing_items = await self.repo.list_knowledge_items(scope=item.scope.value)
        detected_conflicts: list[KnowledgeConflict] = []

        for existing in existing_items:
            if existing.id == item.id:
                continue
            # Simple contradiction heuristic check
            if ("NOT" in item.statement.upper() and existing.statement.upper() in item.statement.upper()) or (
                "NOT" in existing.statement.upper() and item.statement.upper() in existing.statement.upper()
            ):
                conflict = KnowledgeConflict(
                    id=f"conf-{uuid.uuid4().hex[:8]}",
                    knowledge_id_a=existing.id,
                    knowledge_id_b=item.id,
                    conflict_type="CONTRADICTORY_STATEMENT",
                    description=f"Contradictory claim detected between {existing.id} and {item.id}",
                    status=ConflictStatus.OPEN,
                )
                saved_conf = await self.repo.save_conflict(conflict)
                detected_conflicts.append(saved_conf)

                self._publish_event(
                    KnowledgeConflictDetectedEvent(
                        conflict_id=saved_conf.id,
                        knowledge_id_a=existing.id,
                        knowledge_id_b=item.id,
                    )
                )

        return detected_conflicts

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: str,
        winning_knowledge_id: str,
        resolved_by_id: str = "governance_agent",
    ) -> KnowledgeConflict:
        """Resolve a knowledge conflict explicitly without silent deletion."""
        conflict = await self.repo.get_conflict_by_id(conflict_id)
        if not conflict:
            raise ValueError(f"Knowledge conflict {conflict_id} not found")

        conflict.status = ConflictStatus.RESOLVED
        conflict.resolution_strategy = resolution_strategy
        conflict.resolved_by_id = resolved_by_id
        conflict.resolved_at = datetime.now(UTC)

        losing_id = conflict.knowledge_id_b if winning_knowledge_id == conflict.knowledge_id_a else conflict.knowledge_id_a
        losing_item = await self.repo.get_knowledge_item_by_id(losing_id)
        if losing_item:
            losing_item.status = KnowledgeStatus.SUPERSEDED
            losing_item.superseded_at = datetime.now(UTC)
            await self.repo.save_knowledge_item(losing_item)

        saved = await self.repo.save_conflict(conflict)

        self._publish_event(
            KnowledgeConflictResolvedEvent(
                conflict_id=saved.id,
                resolution_strategy=resolution_strategy,
            )
        )

        return saved

    async def mark_knowledge_stale(self, knowledge_id: str, reason: str) -> KnowledgeItem:
        """Mark knowledge item as stale due to workflow, architecture, or policy decay."""
        item = await self.repo.get_knowledge_item_by_id(knowledge_id)
        if not item:
            raise ValueError(f"Knowledge item {knowledge_id} not found")

        item.status = KnowledgeStatus.STALE
        saved = await self.repo.save_knowledge_item(item)

        self._publish_event(
            KnowledgeMarkedStaleEvent(
                knowledge_id=knowledge_id,
                reason=reason,
            )
        )

        return saved

    async def calculate_staleness_decay(self, knowledge_id: str) -> float:
        """Calculate staleness decay score (0.0 fresh -> 1.0 stale) based on elapsed time."""
        item = await self.repo.get_knowledge_item_by_id(knowledge_id)
        if not item:
            return 1.0
        now = datetime.now(UTC)
        created = item.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        elapsed_days = (now - created).total_seconds() / 86400.0
        decay = min(1.0, elapsed_days / 180.0)
        return round(decay, 4)
