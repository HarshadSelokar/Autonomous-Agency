"""SQLAlchemy repository implementation for Phase 18 Institutional Knowledge entities."""

from typing import Sequence
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.experiment import OrganizationalExperiment
from src.domain.knowledge import (
    KnowledgeClaim,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeProcedure,
    KnowledgeProvenance,
    KnowledgeRelationship,
    KnowledgeUsageRecord,
    KnowledgeValidation,
)
from src.infrastructure.models.knowledge_model import (
    KnowledgeClaimModel,
    KnowledgeConflictModel,
    KnowledgeItemModel,
    KnowledgeProcedureModel,
    KnowledgeProvenanceModel,
    KnowledgeRelationshipModel,
    KnowledgeUsageRecordModel,
    KnowledgeValidationModel,
    OrganizationalExperimentModel,
)


class SQLAlchemyKnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------------------------------------------------------
    # Knowledge Items
    # ---------------------------------------------------------
    async def save_knowledge_item(self, item: KnowledgeItem) -> KnowledgeItem:
        model = await self.session.get(KnowledgeItemModel, item.id)
        if model is None:
            model = KnowledgeItemModel.from_domain(item)
            self.session.add(model)
        else:
            updated = KnowledgeItemModel.from_domain(item)
            model.statement = updated.statement
            model.summary = updated.summary
            model.knowledge_type = updated.knowledge_type
            model.scope = updated.scope
            model.scope_id = updated.scope_id
            model.authority = updated.authority
            model.status = updated.status
            model.confidence = updated.confidence
            model.quality_score = updated.quality_score
            model.valid_from = updated.valid_from
            model.valid_until = updated.valid_until
            model.observed_at = updated.observed_at
            model.superseded_at = updated.superseded_at
            model.version = updated.version
            model.metadata_json = updated.metadata_json
        await self.session.flush()
        return model.to_domain()

    async def get_knowledge_item_by_id(self, knowledge_id: str) -> KnowledgeItem | None:
        model = await self.session.get(KnowledgeItemModel, knowledge_id)
        return model.to_domain() if model else None

    async def list_knowledge_items(
        self,
        scope: str | None = None,
        authority: str | None = None,
        status: str | None = None,
        knowledge_type: str | None = None,
    ) -> Sequence[KnowledgeItem]:
        stmt = select(KnowledgeItemModel)
        if scope:
            stmt = stmt.where(KnowledgeItemModel.scope == scope)
        if authority:
            stmt = stmt.where(KnowledgeItemModel.authority == authority)
        if status:
            stmt = stmt.where(KnowledgeItemModel.status == status)
        if knowledge_type:
            stmt = stmt.where(KnowledgeItemModel.knowledge_type == knowledge_type)
        stmt = stmt.order_by(KnowledgeItemModel.created_at.desc())
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def search_knowledge_items(self, query_text: str) -> Sequence[KnowledgeItem]:
        pattern = f"%{query_text}%"
        stmt = select(KnowledgeItemModel).where(
            or_(
                KnowledgeItemModel.statement.ilike(pattern),
                KnowledgeItemModel.summary.ilike(pattern),
            )
        ).order_by(KnowledgeItemModel.confidence.desc())
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Claims & Provenance
    # ---------------------------------------------------------
    async def save_claim(self, claim: KnowledgeClaim) -> KnowledgeClaim:
        model = await self.session.get(KnowledgeClaimModel, claim.id)
        if model is None:
            model = KnowledgeClaimModel.from_domain(claim)
            self.session.add(model)
        else:
            updated = KnowledgeClaimModel.from_domain(claim)
            model.statement = updated.statement
            model.evidence_ids_json = updated.evidence_ids_json
            model.confidence = updated.confidence
            model.authority = updated.authority
            model.status = updated.status
        await self.session.flush()
        return model.to_domain()

    async def get_claim_by_id(self, claim_id: str) -> KnowledgeClaim | None:
        model = await self.session.get(KnowledgeClaimModel, claim_id)
        return model.to_domain() if model else None

    async def list_claims_for_knowledge(self, knowledge_id: str) -> Sequence[KnowledgeClaim]:
        stmt = select(KnowledgeClaimModel).where(KnowledgeClaimModel.knowledge_id == knowledge_id)
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_provenance(self, provenance: KnowledgeProvenance) -> KnowledgeProvenance:
        model = await self.session.get(KnowledgeProvenanceModel, provenance.id)
        if model is None:
            model = KnowledgeProvenanceModel.from_domain(provenance)
            self.session.add(model)
        else:
            updated = KnowledgeProvenanceModel.from_domain(provenance)
            model.source_type = updated.source_type
            model.source_id = updated.source_id
        await self.session.flush()
        return model.to_domain()

    async def get_provenance_by_knowledge_id(self, knowledge_id: str) -> Sequence[KnowledgeProvenance]:
        stmt = select(KnowledgeProvenanceModel).where(KnowledgeProvenanceModel.knowledge_id == knowledge_id)
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Validations & Conflicts
    # ---------------------------------------------------------
    async def save_validation(self, validation: KnowledgeValidation) -> KnowledgeValidation:
        model = await self.session.get(KnowledgeValidationModel, validation.id)
        if model is None:
            model = KnowledgeValidationModel.from_domain(validation)
            self.session.add(model)
        else:
            updated = KnowledgeValidationModel.from_domain(validation)
            model.validation_status = updated.validation_status
            model.confidence_delta = updated.confidence_delta
            model.rationale = updated.rationale
        await self.session.flush()
        return model.to_domain()

    async def list_validations_for_knowledge(self, knowledge_id: str) -> Sequence[KnowledgeValidation]:
        stmt = select(KnowledgeValidationModel).where(KnowledgeValidationModel.knowledge_id == knowledge_id)
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_conflict(self, conflict: KnowledgeConflict) -> KnowledgeConflict:
        model = await self.session.get(KnowledgeConflictModel, conflict.id)
        if model is None:
            model = KnowledgeConflictModel.from_domain(conflict)
            self.session.add(model)
        else:
            updated = KnowledgeConflictModel.from_domain(conflict)
            model.status = updated.status
            model.resolution_strategy = updated.resolution_strategy
            model.resolved_by_id = updated.resolved_by_id
            model.resolved_at = updated.resolved_at
        await self.session.flush()
        return model.to_domain()

    async def get_conflict_by_id(self, conflict_id: str) -> KnowledgeConflict | None:
        model = await self.session.get(KnowledgeConflictModel, conflict_id)
        return model.to_domain() if model else None

    async def list_conflicts_for_knowledge(self, knowledge_id: str) -> Sequence[KnowledgeConflict]:
        stmt = select(KnowledgeConflictModel).where(
            or_(
                KnowledgeConflictModel.knowledge_id_a == knowledge_id,
                KnowledgeConflictModel.knowledge_id_b == knowledge_id,
            )
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def list_open_conflicts(self) -> Sequence[KnowledgeConflict]:
        stmt = select(KnowledgeConflictModel).where(KnowledgeConflictModel.status == "OPEN")
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Relationships & Graph
    # ---------------------------------------------------------
    async def save_relationship(self, relationship: KnowledgeRelationship) -> KnowledgeRelationship:
        model = await self.session.get(KnowledgeRelationshipModel, relationship.id)
        if model is None:
            model = KnowledgeRelationshipModel.from_domain(relationship)
            self.session.add(model)
        else:
            updated = KnowledgeRelationshipModel.from_domain(relationship)
            model.relationship_type = updated.relationship_type
            model.weight = updated.weight
        await self.session.flush()
        return model.to_domain()

    async def list_relationships_for_entity(self, entity_id: str) -> Sequence[KnowledgeRelationship]:
        stmt = select(KnowledgeRelationshipModel).where(
            or_(
                KnowledgeRelationshipModel.source_id == entity_id,
                KnowledgeRelationshipModel.target_id == entity_id,
            )
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Procedures & Experiments
    # ---------------------------------------------------------
    async def save_procedure(self, procedure: KnowledgeProcedure) -> KnowledgeProcedure:
        model = await self.session.get(KnowledgeProcedureModel, procedure.id)
        if model is None:
            model = KnowledgeProcedureModel.from_domain(procedure)
            self.session.add(model)
        else:
            updated = KnowledgeProcedureModel.from_domain(procedure)
            model.title = updated.title
            model.purpose = updated.purpose
            model.prerequisites_json = updated.prerequisites_json
            model.steps_json = updated.steps_json
            model.expected_outcome = updated.expected_outcome
            model.verification_criteria_json = updated.verification_criteria_json
            model.failure_conditions_json = updated.failure_conditions_json
            model.rollback_steps_json = updated.rollback_steps_json
            model.scope = updated.scope
            model.version = updated.version
            model.validation_status = updated.validation_status
            model.is_governance_approved = updated.is_governance_approved
        await self.session.flush()
        return model.to_domain()

    async def get_procedure_by_id(self, procedure_id: str) -> KnowledgeProcedure | None:
        model = await self.session.get(KnowledgeProcedureModel, procedure_id)
        return model.to_domain() if model else None

    async def list_procedures(self, scope: str | None = None) -> Sequence[KnowledgeProcedure]:
        stmt = select(KnowledgeProcedureModel)
        if scope:
            stmt = stmt.where(KnowledgeProcedureModel.scope == scope)
        stmt = stmt.order_by(KnowledgeProcedureModel.version.desc())
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_experiment(self, experiment: OrganizationalExperiment) -> OrganizationalExperiment:
        model = await self.session.get(OrganizationalExperimentModel, experiment.id)
        if model is None:
            model = OrganizationalExperimentModel.from_domain(experiment)
            self.session.add(model)
        else:
            updated = OrganizationalExperimentModel.from_domain(experiment)
            model.status = updated.status
            model.results_json = updated.results_json
            model.conclusion = updated.conclusion
            model.governance_approval_id = updated.governance_approval_id
            model.started_at = updated.started_at
            model.completed_at = updated.completed_at
        await self.session.flush()
        return model.to_domain()

    async def get_experiment_by_id(self, experiment_id: str) -> OrganizationalExperiment | None:
        model = await self.session.get(OrganizationalExperimentModel, experiment_id)
        return model.to_domain() if model else None

    async def list_experiments(self, status: str | None = None) -> Sequence[OrganizationalExperiment]:
        stmt = select(OrganizationalExperimentModel)
        if status:
            stmt = stmt.where(OrganizationalExperimentModel.status == status)
        stmt = stmt.order_by(OrganizationalExperimentModel.created_at.desc())
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Usage Records
    # ---------------------------------------------------------
    async def save_usage_record(self, record: KnowledgeUsageRecord) -> KnowledgeUsageRecord:
        model = await self.session.get(KnowledgeUsageRecordModel, record.id)
        if model is None:
            model = KnowledgeUsageRecordModel.from_domain(record)
            self.session.add(model)
        else:
            updated = KnowledgeUsageRecordModel.from_domain(record)
            model.outcome_status = updated.outcome_status
            model.effectiveness_score = updated.effectiveness_score
        await self.session.flush()
        return model.to_domain()

    async def list_usage_records_for_knowledge(self, knowledge_id: str) -> Sequence[KnowledgeUsageRecord]:
        stmt = select(KnowledgeUsageRecordModel).where(KnowledgeUsageRecordModel.knowledge_id == knowledge_id)
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]
