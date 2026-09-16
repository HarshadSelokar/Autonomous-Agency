"""
OrganizationalExperimentService for Phase 18.

Manages governed, isolated organizational experiments and converts verified conclusions
into candidate institutional knowledge.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from src.application.knowledge_validation_service import KnowledgeValidationService
from src.domain.events import (
    DomainEvent,
    OrganizationalExperimentCompletedEvent,
    OrganizationalExperimentStartedEvent,
)
from src.domain.experiment import ExperimentStatus, OrganizationalExperiment
from src.domain.knowledge import KnowledgeAuthority, KnowledgeItem, KnowledgeScope, KnowledgeStatus, KnowledgeType
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository


class OrganizationalExperimentService:
    def __init__(
        self,
        repository: SQLAlchemyKnowledgeRepository,
        validation_service: KnowledgeValidationService,
        governance_service: Any | None = None,
        outbox_publisher: Any | None = None,
    ) -> None:
        self.repo = repository
        self.validation_svc = validation_service
        self.governance_svc = governance_service
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def propose_experiment(
        self,
        title: str,
        hypothesis: str,
        scope: str = "COMPANY",
        baseline_metrics: dict[str, Any] | None = None,
        treatment_params: dict[str, Any] | None = None,
        success_criteria: dict[str, Any] | None = None,
        risk_level: str = "MEDIUM",
        duration_hours: int = 24,
    ) -> OrganizationalExperiment:
        """Propose a new isolated organizational experiment."""
        exp = OrganizationalExperiment(
            id=f"exp-{uuid.uuid4().hex[:8]}",
            title=title,
            hypothesis=hypothesis,
            scope=scope,
            baseline_metrics=baseline_metrics or {},
            treatment_params=treatment_params or {},
            success_criteria=success_criteria or {},
            risk_level=risk_level,
            duration_hours=duration_hours,
            status=ExperimentStatus.PROPOSED,
            is_isolated=True,  # Invariant
            created_at=datetime.now(UTC),
        )

        return await self.repo.save_experiment(exp)

    async def start_experiment(
        self,
        experiment_id: str,
        governance_approval_id: str | None = None,
    ) -> OrganizationalExperiment:
        """Start an active experiment."""
        exp = await self.repo.get_experiment_by_id(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")

        if exp.risk_level in ("HIGH", "CRITICAL") and not governance_approval_id:
            exp.status = ExperimentStatus.AWAITING_GOVERNANCE
            await self.repo.save_experiment(exp)
            raise ValueError(f"Experiment {experiment_id} requires Phase 11 governance approval due to risk level {exp.risk_level}")

        exp.status = ExperimentStatus.ACTIVE
        exp.governance_approval_id = governance_approval_id
        exp.started_at = datetime.now(UTC)

        saved = await self.repo.save_experiment(exp)

        self._publish_event(
            OrganizationalExperimentStartedEvent(
                experiment_id=saved.id,
                title=saved.title,
            )
        )

        return saved

    async def complete_experiment(
        self,
        experiment_id: str,
        results: dict[str, Any],
        conclusion: str,
    ) -> OrganizationalExperiment:
        """Complete an active experiment and record outcomes."""
        exp = await self.repo.get_experiment_by_id(experiment_id)
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")

        exp.status = ExperimentStatus.COMPLETED
        exp.results = results
        exp.conclusion = conclusion
        exp.completed_at = datetime.now(UTC)

        saved = await self.repo.save_experiment(exp)

        self._publish_event(
            OrganizationalExperimentCompletedEvent(
                experiment_id=saved.id,
                title=saved.title,
                conclusion=saved.conclusion,
            )
        )

        return saved

    async def convert_experiment_to_knowledge_candidate(
        self,
        experiment_id: str,
    ) -> KnowledgeItem:
        """
        Convert verified experiment conclusion into a candidate KnowledgeItem.
        CRITICAL INVARIANT: Experiment results DO NOT automatically become production policy.
        """
        exp = await self.repo.get_experiment_by_id(experiment_id)
        if not exp or exp.status != ExperimentStatus.COMPLETED:
            raise ValueError(f"Completed experiment {experiment_id} not found")

        statement = f"Experiment '{exp.title}' concluded: {exp.conclusion}"
        item = KnowledgeItem(
            id=f"k-exp-{uuid.uuid4().hex[:8]}",
            statement=statement,
            summary=f"Experiment conclusion for {exp.title}",
            knowledge_type=KnowledgeType.LESSON,
            scope=KnowledgeScope.COMPANY,
            authority=KnowledgeAuthority.EVIDENCE_BACKED,
            status=KnowledgeStatus.CANDIDATE,  # Candidate, not automatically policy
            confidence=0.8,
            metadata={"experiment_id": exp.id, "results": exp.results},
        )

        return await self.repo.save_knowledge_item(item)
