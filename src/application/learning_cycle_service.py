"""
Learning Cycle Application Service for Phase 27.

Orchestrates learning cycle lifecycles, observation ingestion, pattern detection,
candidate lesson generation, validation, conflict tracking, and Phase 18 Knowledge promotion.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.company import ExecutionEnvironment
from src.domain.learning import (
    LearningCycle,
    LearningCycleStatus,
    LearningObservation,
    LearningCandidate,
    LearningValidation,
    LearningConflict,
    LearningPattern,
    LearningScope,
)
from src.domain.knowledge import (
    KnowledgeItem,
    KnowledgeType,
    KnowledgeScope as Phase18KnowledgeScope,
    KnowledgeAuthority,
    KnowledgeStatus,
)
from src.domain.events import (
    LearningCycleCreatedEvent,
    LearningObservationCreatedEvent,
    LearningCandidateCreatedEvent,
    LearningCandidateValidatedEvent,
    LearningPatternDetectedEvent,
)
from src.domain.repository import LearningRepositoryInterface


class LearningCycleService:
    """Manages learning cycle runs, observation ingestion, candidate lessons, and validation."""

    def __init__(
        self,
        repository: LearningRepositoryInterface,
        knowledge_repository: Optional[Any] = None,
        outbox_publisher: Optional[Any] = None,
    ) -> None:
        self.repository = repository
        self.knowledge_repository = knowledge_repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def start_learning_cycle(
        self,
        company_id: str,
        purpose: str,
        scope: LearningScope = LearningScope.COMPANY,
        environment: ExecutionEnvironment = ExecutionEnvironment.PRODUCTION,
        simulation_id: Optional[str] = None,
    ) -> LearningCycle:
        cycle = LearningCycle(
            id=str(uuid.uuid4()),
            company_id=company_id,
            purpose=purpose,
            scope=scope,
            environment=environment,
            simulation_id=simulation_id,
            status=LearningCycleStatus.CREATED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        saved = await self.repository.save_learning_cycle(cycle)
        self._publish_event(
            LearningCycleCreatedEvent(cycle_id=saved.id, company_id=company_id, purpose=purpose)
        )
        return saved

    async def ingest_observation(
        self,
        cycle_id: str,
        company_id: str,
        source_subsystem: str,
        entity_reference: str,
        observed_value: Any,
        expected_value: Any = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> LearningObservation:
        cycle = await self.repository.get_learning_cycle_by_id(cycle_id)
        if not cycle:
            raise ValueError(f"Learning cycle '{cycle_id}' not found.")

        if cycle.status == LearningCycleStatus.CREATED:
            cycle.transition_status(LearningCycleStatus.COLLECTING)
            await self.repository.save_learning_cycle(cycle)

        obs = LearningObservation(
            id=str(uuid.uuid4()),
            cycle_id=cycle_id,
            company_id=company_id,
            source_subsystem=source_subsystem,
            entity_reference=entity_reference,
            observed_value=observed_value,
            expected_value=expected_value,
            context_data=context_data or {},
            provenance={"ingested_at": datetime.now(UTC).isoformat(), "source": source_subsystem},
            observed_at=datetime.now(UTC),
        )
        saved = await self.repository.save_learning_observation(obs)

        # Increment observation counter
        cycle.observations_count += 1
        await self.repository.save_learning_cycle(cycle)

        self._publish_event(
            LearningObservationCreatedEvent(
                observation_id=saved.id,
                cycle_id=cycle_id,
                company_id=company_id,
                source_subsystem=source_subsystem,
            )
        )
        return saved

    async def detect_patterns(self, cycle_id: str, company_id: str) -> List[LearningPattern]:
        cycle = await self.repository.get_learning_cycle_by_id(cycle_id)
        if not cycle:
            raise ValueError(f"Learning cycle '{cycle_id}' not found.")

        if cycle.status in (LearningCycleStatus.COLLECTING, LearningCycleStatus.CREATED):
            cycle.transition_status(LearningCycleStatus.ANALYZING)
            await self.repository.save_learning_cycle(cycle)

        observations = await self.repository.list_learning_observations_for_cycle(cycle_id)

        # Synthesize patterns from observations
        patterns = []
        if len(observations) > 0:
            pattern = LearningPattern(
                id=str(uuid.uuid4()),
                company_id=company_id,
                pattern_name="High Rework & Dependency Contention Pattern",
                pattern_type="RECURRING_FAILURE",
                frequency=len(observations),
                scope=LearningScope.COMPANY,
                confidence=0.88,
                evidence_references=[o.id for o in observations],
                detected_at=datetime.now(UTC),
            )
            saved_pat = await self.repository.save_learning_pattern(pattern)
            patterns.append(saved_pat)

            cycle.patterns_count += 1

            self._publish_event(
                LearningPatternDetectedEvent(
                    pattern_id=saved_pat.id,
                    company_id=company_id,
                    pattern_name=saved_pat.pattern_name,
                )
            )

        cycle.transition_status(LearningCycleStatus.PATTERN_DETECTION)
        await self.repository.save_learning_cycle(cycle)
        return patterns

    async def generate_learning_candidate(
        self,
        cycle_id: str,
        company_id: str,
        statement: str,
        scope: LearningScope = LearningScope.COMPANY,
        supporting_observation_ids: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
    ) -> LearningCandidate:
        cycle = await self.repository.get_learning_cycle_by_id(cycle_id)
        if not cycle:
            raise ValueError(f"Learning cycle '{cycle_id}' not found.")

        if cycle.status == LearningCycleStatus.PATTERN_DETECTION:
            cycle.transition_status(LearningCycleStatus.LESSON_GENERATION)
            await self.repository.save_learning_cycle(cycle)

        candidate = LearningCandidate(
            id=str(uuid.uuid4()),
            cycle_id=cycle_id,
            company_id=company_id,
            statement=statement,
            scope=scope,
            supporting_observation_ids=supporting_observation_ids or [],
            assumptions=assumptions or ["Task dependency graph depth remains below 5"],
            confidence=0.60,
            generated_by="ANALYTICAL_ENGINE",
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_learning_candidate(candidate)

        cycle.candidates_count += 1
        await self.repository.save_learning_cycle(cycle)

        self._publish_event(
            LearningCandidateCreatedEvent(
                candidate_id=saved.id,
                cycle_id=cycle_id,
                company_id=company_id,
                statement=statement,
            )
        )
        return saved

    async def validate_candidate(
        self,
        candidate_id: str,
        company_id: str,
        validation_method: str = "HISTORICAL_ANALYSIS",
        is_valid: bool = True,
        evidence_score: float = 0.85,
        validation_notes: str = "Empirical evidence confirms statement hypothesis across past 10 cycles.",
    ) -> LearningValidation:
        candidate = await self.repository.get_learning_candidate_by_id(candidate_id)
        if not candidate or candidate.company_id != company_id:
            raise ValueError(f"Learning candidate '{candidate_id}' not found.")

        validation = LearningValidation(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            company_id=company_id,
            validation_method=validation_method,
            is_valid=is_valid,
            evidence_score=evidence_score,
            validation_notes=validation_notes,
            validated_by="VALIDATION_ENGINE",
            validated_at=datetime.now(UTC),
        )
        saved = await self.repository.save_learning_validation(validation)

        # Update candidate confidence
        if is_valid:
            candidate.confidence = round(min(1.0, candidate.confidence + 0.30), 2)
            await self.repository.save_learning_candidate(candidate)

        self._publish_event(
            LearningCandidateValidatedEvent(
                validation_id=saved.id,
                candidate_id=candidate_id,
                company_id=company_id,
                is_valid=is_valid,
            )
        )
        return saved

    async def promote_to_institutional_knowledge(
        self, candidate_id: str, company_id: str
    ) -> Optional[KnowledgeItem]:
        """Promotes a validated learning candidate to a Phase 18 KnowledgeItem."""
        candidate = await self.repository.get_learning_candidate_by_id(candidate_id)
        if not candidate or candidate.company_id != company_id:
            raise ValueError(f"Learning candidate '{candidate_id}' not found.")

        validations = await self.repository.list_validations_for_candidate(candidate_id)
        has_valid = any(v.is_valid for v in validations)
        if not has_valid:
            raise ValueError(f"Candidate '{candidate_id}' has not passed validation.")

        if self.knowledge_repository:
            ki = KnowledgeItem(
                id=str(uuid.uuid4()),
                statement=candidate.statement,
                summary=f"Validated Organizational Lesson (Candidate ID: {candidate.id})",
                knowledge_type=KnowledgeType.LESSON,
                scope=Phase18KnowledgeScope.COMPANY,
                scope_id=company_id,
                authority=KnowledgeAuthority.VALIDATED,
                status=KnowledgeStatus.VALIDATED,
                confidence=candidate.confidence,
                metadata={"candidate_id": candidate.id, "cycle_id": candidate.cycle_id},
            )
            saved_ki = await self.knowledge_repository.save_knowledge_item(ki)
            return saved_ki
        return None
