"""
InstitutionalLearningService for Phase 18.

Handles cross-domain learning extraction across Failure, Success, Forecast, Decision,
Workforce, Tool & Model, and Strategy domain events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from src.application.knowledge_validation_service import KnowledgeValidationService
from src.domain.events import DomainEvent, KnowledgeCandidateDiscoveredEvent
from src.domain.knowledge import (
    KnowledgeAuthority,
    KnowledgeItem,
    KnowledgeProvenance,
    KnowledgeScope,
    KnowledgeStatus,
    KnowledgeType,
)
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository


class InstitutionalLearningService:
    def __init__(
        self,
        repository: SQLAlchemyKnowledgeRepository,
        validation_service: KnowledgeValidationService,
        outbox_publisher: Any | None = None,
    ) -> None:
        self.repo = repository
        self.validation_svc = validation_service
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def learn_from_failure(
        self,
        task_id: str,
        failure_description: str,
        recovery_strategy_used: str,
        recovery_outcome: str = "SUCCESS",
        evidence_ids: list[str] | None = None,
    ) -> KnowledgeItem:
        """Extract a failure lesson from Phase 10 verification/recovery outcomes."""
        statement = f"Task failure on {task_id}: {failure_description}. Resolved via {recovery_strategy_used}."
        item = KnowledgeItem(
            id=f"k-fail-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Failure recovery lesson for {task_id}",
            knowledge_type=KnowledgeType.LESSON,
            scope=KnowledgeScope.TASK,
            scope_id=task_id,
            authority=KnowledgeAuthority.UNVERIFIED,
            status=KnowledgeStatus.CANDIDATE,
            confidence=0.6,
        )

        saved_item = await self.repo.save_knowledge_item(item)

        prov = KnowledgeProvenance(
            knowledge_id=saved_item.id,
            source_type="TASK_FAILURE_RECOVERY",
            source_id=task_id,
            task_id=task_id,
        )
        await self.repo.save_provenance(prov)

        self._publish_event(
            KnowledgeCandidateDiscoveredEvent(
                knowledge_id=saved_item.id,
                statement=saved_item.statement,
                knowledge_type=saved_item.knowledge_type.value,
                scope=saved_item.scope.value,
            )
        )

        return saved_item

    async def learn_from_success(
        self,
        task_id: str,
        success_description: str,
        verification_id: str,
        evidence_ids: list[str] | None = None,
    ) -> KnowledgeItem:
        """Extract a success pattern from verified task completion."""
        statement = f"Task {task_id} successfully verified via {verification_id}: {success_description}."
        item = KnowledgeItem(
            id=f"k-succ-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Verified success pattern for {task_id}",
            knowledge_type=KnowledgeType.PATTERN,
            scope=KnowledgeScope.TASK,
            scope_id=task_id,
            authority=KnowledgeAuthority.EVIDENCE_BACKED if evidence_ids else KnowledgeAuthority.OBSERVED,
            status=KnowledgeStatus.CANDIDATE,
            confidence=0.8,
        )

        saved_item = await self.repo.save_knowledge_item(item)

        prov = KnowledgeProvenance(
            knowledge_id=saved_item.id,
            source_type="VERIFIED_SUCCESS",
            source_id=task_id,
            task_id=task_id,
            verification_id=verification_id,
        )
        await self.repo.save_provenance(prov)

        self._publish_event(
            KnowledgeCandidateDiscoveredEvent(
                knowledge_id=saved_item.id,
                statement=saved_item.statement,
                knowledge_type=saved_item.knowledge_type.value,
                scope=saved_item.scope.value,
            )
        )

        return saved_item

    async def learn_from_forecast(
        self,
        forecast_id: str,
        metric_name: str,
        predicted_value: float,
        actual_value: float,
        error_pct: float,
    ) -> KnowledgeItem:
        """Extract a forecast lesson from Phase 17 prediction evaluation."""
        statement = f"Forecast {forecast_id} for {metric_name} predicted {predicted_value} vs actual {actual_value} (Error: {error_pct:.1f}%)."
        item = KnowledgeItem(
            id=f"k-fcst-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Forecast calibration lesson for {metric_name}",
            knowledge_type=KnowledgeType.PREDICTION_LESSON,
            scope=KnowledgeScope.COMPANY,
            authority=KnowledgeAuthority.EVIDENCE_BACKED,
            status=KnowledgeStatus.CANDIDATE,
            confidence=0.75,
        )

        saved_item = await self.repo.save_knowledge_item(item)
        return saved_item

    async def learn_from_decision(
        self,
        decision_id: str,
        title: str,
        expected_outcome: str,
        actual_outcome: str,
        effectiveness_score: float,
    ) -> KnowledgeItem:
        """Extract a decision effectiveness lesson from Phase 6 decision tracking."""
        statement = f"Decision {decision_id} ('{title}'): Expected '{expected_outcome}', Actual '{actual_outcome}' (Score: {effectiveness_score})."
        item = KnowledgeItem(
            id=f"k-dec-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Decision outcome lesson for {title}",
            knowledge_type=KnowledgeType.DECISION_LESSON,
            scope=KnowledgeScope.COMPANY,
            authority=KnowledgeAuthority.EVIDENCE_BACKED,
            status=KnowledgeStatus.CANDIDATE,
            confidence=0.85,
        )

        saved_item = await self.repo.save_knowledge_item(item)
        return saved_item

    async def learn_from_workforce_allocation(
        self,
        team_id: str,
        capability: str,
        outcome_status: str,
        lesson_text: str,
    ) -> KnowledgeItem:
        """
        Extract workforce allocation capability pattern from Phase 15.
        CRITICAL INVARIANT: Workforce learning is strictly non-punitive and used for capability matching.
        """
        statement = f"Team {team_id} allocation for capability {capability} resulted in {outcome_status}: {lesson_text}"
        item = KnowledgeItem(
            id=f"k-wf-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Workforce capability pattern for {capability}",
            knowledge_type=KnowledgeType.WORKFORCE_LESSON,
            scope=KnowledgeScope.TEAM,
            scope_id=team_id,
            authority=KnowledgeAuthority.OBSERVED,
            status=KnowledgeStatus.CANDIDATE,
            confidence=0.7,
        )

        saved_item = await self.repo.save_knowledge_item(item)
        return saved_item

    async def learn_from_tool_and_model(
        self,
        tool_or_model_id: str,
        entity_type: str,  # TOOL or MODEL
        workload_type: str,
        latency_ms: float,
        success_rate: float,
    ) -> KnowledgeItem:
        """Extract tool or model performance insight for Phase 8 / Phase 12 selection optimization."""
        k_type = KnowledgeType.TOOL_LESSON if entity_type == "TOOL" else KnowledgeType.MODEL_LESSON
        statement = f"{entity_type} {tool_or_model_id} on workload {workload_type}: Avg Latency {latency_ms}ms, Success Rate {success_rate * 100:.1f}%."
        item = KnowledgeItem(
            id=f"k-tm-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Performance pattern for {tool_or_model_id}",
            knowledge_type=k_type,
            scope=KnowledgeScope.TOOL if entity_type == "TOOL" else KnowledgeScope.MODEL,
            scope_id=tool_or_model_id,
            authority=KnowledgeAuthority.EVIDENCE_BACKED,
            status=KnowledgeStatus.CANDIDATE,
            confidence=0.9,
        )

        saved_item = await self.repo.save_knowledge_item(item)
        return saved_item

    async def learn_from_strategy_initiative(
        self,
        initiative_id: str,
        title: str,
        target_metric: str,
        achieved_value: float,
        target_value: float,
    ) -> KnowledgeItem:
        """Extract strategic learning from Phase 16 strategic initiative outcomes."""
        statement = f"Strategic Initiative '{title}' ({initiative_id}) for {target_metric}: Achieved {achieved_value} vs Target {target_value}."
        item = KnowledgeItem(
            id=f"k-strat-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Strategic initiative outcome lesson for '{title}'",
            knowledge_type=KnowledgeType.STRATEGY_LESSON,
            scope=KnowledgeScope.COMPANY,
            authority=KnowledgeAuthority.EVIDENCE_BACKED,
            status=KnowledgeStatus.CANDIDATE,
            confidence=0.88,
        )

        saved_item = await self.repo.save_knowledge_item(item)
        return saved_item
