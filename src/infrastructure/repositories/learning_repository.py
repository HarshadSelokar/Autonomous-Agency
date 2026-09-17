"""
SQLAlchemy Implementation of LearningRepositoryInterface for Phase 27.
"""

import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.company import ExecutionEnvironment
from src.domain.learning import (
    LearningCycle,
    LearningCycleStatus,
    LearningObservation,
    ExpectedVsActualComparison,
    LearningCandidate,
    LearningValidation,
    LearningConflict,
    LearningPattern,
    ImprovementOpportunity,
    AdaptationProposal,
    AdaptationStatus,
    AdaptationType,
    AdaptationRiskLevel,
    AdaptationEvaluation,
    AdaptationExecution,
    AdaptationOutcome,
    AdaptationImpactAssessment,
    LearningScope,
)
from src.domain.repository import LearningRepositoryInterface
from src.infrastructure.models.learning_model import (
    LearningCycleModel,
    LearningObservationModel,
    ExpectedVsActualComparisonModel,
    LearningCandidateModel,
    LearningValidationModel,
    LearningConflictModel,
    LearningPatternModel,
    ImprovementOpportunityModel,
    AdaptationProposalModel,
    AdaptationEvaluationModel,
    AdaptationExecutionModel,
    AdaptationOutcomeModel,
    AdaptationImpactAssessmentModel,
)


class SQLAlchemyLearningRepository(LearningRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # 1. Learning Cycle
    async def save_learning_cycle(self, cycle: LearningCycle) -> LearningCycle:
        stmt = select(LearningCycleModel).where(LearningCycleModel.id == cycle.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = LearningCycleModel(id=cycle.id)
            self.session.add(model)

        model.company_id = cycle.company_id
        model.purpose = cycle.purpose
        model.scope = cycle.scope.value if isinstance(cycle.scope, Enum) else cycle.scope
        model.environment = cycle.environment.value if isinstance(cycle.environment, Enum) else cycle.environment
        model.simulation_id = cycle.simulation_id
        model.status = cycle.status.value if isinstance(cycle.status, Enum) else cycle.status
        model.correlation_id = cycle.correlation_id
        model.observations_count = cycle.observations_count
        model.patterns_count = cycle.patterns_count
        model.candidates_count = cycle.candidates_count
        model.updated_at = datetime.now(UTC)

        await self.session.flush()
        return cycle

    async def get_learning_cycle_by_id(self, cycle_id: str) -> Optional[LearningCycle]:
        stmt = select(LearningCycleModel).where(LearningCycleModel.id == cycle_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return LearningCycle(
            id=m.id,
            company_id=m.company_id,
            purpose=m.purpose,
            scope=LearningScope(m.scope),
            environment=ExecutionEnvironment(m.environment),
            simulation_id=m.simulation_id,
            status=LearningCycleStatus(m.status),
            correlation_id=m.correlation_id,
            observations_count=m.observations_count,
            patterns_count=m.patterns_count,
            candidates_count=m.candidates_count,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def list_learning_cycles_for_company(self, company_id: str) -> List[LearningCycle]:
        stmt = select(LearningCycleModel).where(LearningCycleModel.company_id == company_id).order_by(LearningCycleModel.created_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            LearningCycle(
                id=m.id,
                company_id=m.company_id,
                purpose=m.purpose,
                scope=LearningScope(m.scope),
                environment=ExecutionEnvironment(m.environment),
                simulation_id=m.simulation_id,
                status=LearningCycleStatus(m.status),
                correlation_id=m.correlation_id,
                observations_count=m.observations_count,
                patterns_count=m.patterns_count,
                candidates_count=m.candidates_count,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # 2. Learning Observation
    async def save_learning_observation(self, observation: LearningObservation) -> LearningObservation:
        stmt = select(LearningObservationModel).where(LearningObservationModel.id == observation.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = LearningObservationModel(id=observation.id)
            self.session.add(model)

        model.cycle_id = observation.cycle_id
        model.company_id = observation.company_id
        model.source_subsystem = observation.source_subsystem
        model.entity_reference = observation.entity_reference
        model.observed_value_json = json.dumps(observation.observed_value)
        model.expected_value_json = json.dumps(observation.expected_value)
        model.context_data_json = json.dumps(observation.context_data)
        model.provenance_json = json.dumps(observation.provenance)
        model.observed_at = observation.observed_at

        await self.session.flush()
        return observation

    async def list_learning_observations_for_cycle(self, cycle_id: str) -> List[LearningObservation]:
        stmt = select(LearningObservationModel).where(LearningObservationModel.cycle_id == cycle_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            LearningObservation(
                id=m.id,
                cycle_id=m.cycle_id,
                company_id=m.company_id,
                source_subsystem=m.source_subsystem,
                entity_reference=m.entity_reference,
                observed_value=json.loads(m.observed_value_json) if m.observed_value_json else None,
                expected_value=json.loads(m.expected_value_json) if m.expected_value_json else None,
                context_data=json.loads(m.context_data_json) if m.context_data_json else {},
                provenance=json.loads(m.provenance_json) if m.provenance_json else {},
                observed_at=m.observed_at,
            )
            for m in models
        ]

    # 3. Expected Vs Actual Comparison
    async def save_expected_vs_actual_comparison(self, comparison: ExpectedVsActualComparison) -> ExpectedVsActualComparison:
        stmt = select(ExpectedVsActualComparisonModel).where(ExpectedVsActualComparisonModel.id == comparison.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = ExpectedVsActualComparisonModel(id=comparison.id)
            self.session.add(model)

        model.cycle_id = comparison.cycle_id
        model.company_id = comparison.company_id
        model.domain = comparison.domain
        model.metric_name = comparison.metric_name
        model.expected_value = comparison.expected_value
        model.actual_value = comparison.actual_value
        model.variance = comparison.variance
        model.variance_percentage = comparison.variance_percentage
        model.confidence = comparison.confidence
        model.context_json = json.dumps(comparison.context)
        model.evaluated_at = comparison.evaluated_at

        await self.session.flush()
        return comparison

    async def list_comparisons_for_cycle(self, cycle_id: str) -> List[ExpectedVsActualComparison]:
        stmt = select(ExpectedVsActualComparisonModel).where(ExpectedVsActualComparisonModel.cycle_id == cycle_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ExpectedVsActualComparison(
                id=m.id,
                cycle_id=m.cycle_id,
                company_id=m.company_id,
                domain=m.domain,
                metric_name=m.metric_name,
                expected_value=m.expected_value,
                actual_value=m.actual_value,
                variance=m.variance,
                variance_percentage=m.variance_percentage,
                confidence=m.confidence,
                context=json.loads(m.context_json) if m.context_json else {},
                evaluated_at=m.evaluated_at,
            )
            for m in models
        ]

    # 4. Learning Candidate
    async def save_learning_candidate(self, candidate: LearningCandidate) -> LearningCandidate:
        stmt = select(LearningCandidateModel).where(LearningCandidateModel.id == candidate.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = LearningCandidateModel(id=candidate.id)
            self.session.add(model)

        model.cycle_id = candidate.cycle_id
        model.company_id = candidate.company_id
        model.statement = candidate.statement
        model.scope = candidate.scope.value if isinstance(candidate.scope, Enum) else candidate.scope
        model.supporting_observation_ids_json = json.dumps(candidate.supporting_observation_ids)
        model.counterexamples_json = json.dumps(candidate.counterexamples)
        model.assumptions_json = json.dumps(candidate.assumptions)
        model.confidence = candidate.confidence
        model.generated_by = candidate.generated_by
        model.created_at = candidate.created_at

        await self.session.flush()
        return candidate

    async def get_learning_candidate_by_id(self, candidate_id: str) -> Optional[LearningCandidate]:
        stmt = select(LearningCandidateModel).where(LearningCandidateModel.id == candidate_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return LearningCandidate(
            id=m.id,
            cycle_id=m.cycle_id,
            company_id=m.company_id,
            statement=m.statement,
            scope=LearningScope(m.scope),
            supporting_observation_ids=json.loads(m.supporting_observation_ids_json) if m.supporting_observation_ids_json else [],
            counterexamples=json.loads(m.counterexamples_json) if m.counterexamples_json else [],
            assumptions=json.loads(m.assumptions_json) if m.assumptions_json else [],
            confidence=m.confidence,
            generated_by=m.generated_by,
            created_at=m.created_at,
        )

    async def list_learning_candidates_for_company(self, company_id: str) -> List[LearningCandidate]:
        stmt = select(LearningCandidateModel).where(LearningCandidateModel.company_id == company_id).order_by(LearningCandidateModel.created_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            LearningCandidate(
                id=m.id,
                cycle_id=m.cycle_id,
                company_id=m.company_id,
                statement=m.statement,
                scope=LearningScope(m.scope),
                supporting_observation_ids=json.loads(m.supporting_observation_ids_json) if m.supporting_observation_ids_json else [],
                counterexamples=json.loads(m.counterexamples_json) if m.counterexamples_json else [],
                assumptions=json.loads(m.assumptions_json) if m.assumptions_json else [],
                confidence=m.confidence,
                generated_by=m.generated_by,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 5. Learning Validation
    async def save_learning_validation(self, validation: LearningValidation) -> LearningValidation:
        stmt = select(LearningValidationModel).where(LearningValidationModel.id == validation.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = LearningValidationModel(id=validation.id)
            self.session.add(model)

        model.candidate_id = validation.candidate_id
        model.company_id = validation.company_id
        model.validation_method = validation.validation_method
        model.is_valid = validation.is_valid
        model.evidence_score = validation.evidence_score
        model.validation_notes = validation.validation_notes
        model.validated_by = validation.validated_by
        model.validated_at = validation.validated_at

        await self.session.flush()
        return validation

    async def list_validations_for_candidate(self, candidate_id: str) -> List[LearningValidation]:
        stmt = select(LearningValidationModel).where(LearningValidationModel.candidate_id == candidate_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            LearningValidation(
                id=m.id,
                candidate_id=m.candidate_id,
                company_id=m.company_id,
                validation_method=m.validation_method,
                is_valid=m.is_valid,
                evidence_score=m.evidence_score,
                validation_notes=m.validation_notes,
                validated_by=m.validated_by,
                validated_at=m.validated_at,
            )
            for m in models
        ]

    # 6. Learning Conflict
    async def save_learning_conflict(self, conflict: LearningConflict) -> LearningConflict:
        stmt = select(LearningConflictModel).where(LearningConflictModel.id == conflict.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = LearningConflictModel(id=conflict.id)
            self.session.add(model)

        model.company_id = conflict.company_id
        model.lesson_a_id = conflict.lesson_a_id
        model.lesson_b_id = conflict.lesson_b_id
        model.conflict_summary = conflict.conflict_summary
        model.context_discrepancies_json = json.dumps(conflict.context_discrepancies)
        model.status = conflict.status
        model.detected_at = conflict.detected_at

        await self.session.flush()
        return conflict

    async def list_open_conflicts_for_company(self, company_id: str) -> List[LearningConflict]:
        stmt = select(LearningConflictModel).where(LearningConflictModel.company_id == company_id, LearningConflictModel.status == "OPEN")
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            LearningConflict(
                id=m.id,
                company_id=m.company_id,
                lesson_a_id=m.lesson_a_id,
                lesson_b_id=m.lesson_b_id,
                conflict_summary=m.conflict_summary,
                context_discrepancies=json.loads(m.context_discrepancies_json) if m.context_discrepancies_json else [],
                status=m.status,
                detected_at=m.detected_at,
            )
            for m in models
        ]

    # 7. Learning Pattern
    async def save_learning_pattern(self, pattern: LearningPattern) -> LearningPattern:
        stmt = select(LearningPatternModel).where(LearningPatternModel.id == pattern.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = LearningPatternModel(id=pattern.id)
            self.session.add(model)

        model.company_id = pattern.company_id
        model.pattern_name = pattern.pattern_name
        model.pattern_type = pattern.pattern_type
        model.frequency = pattern.frequency
        model.scope = pattern.scope.value if isinstance(pattern.scope, Enum) else pattern.scope
        model.confidence = pattern.confidence
        model.evidence_references_json = json.dumps(pattern.evidence_references)
        model.detected_at = pattern.detected_at

        await self.session.flush()
        return pattern

    async def list_learning_patterns_for_company(self, company_id: str) -> List[LearningPattern]:
        stmt = select(LearningPatternModel).where(LearningPatternModel.company_id == company_id).order_by(LearningPatternModel.detected_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            LearningPattern(
                id=m.id,
                company_id=m.company_id,
                pattern_name=m.pattern_name,
                pattern_type=m.pattern_type,
                frequency=m.frequency,
                scope=LearningScope(m.scope),
                confidence=m.confidence,
                evidence_references=json.loads(m.evidence_references_json) if m.evidence_references_json else [],
                detected_at=m.detected_at,
            )
            for m in models
        ]

    # 8. Improvement Opportunity
    async def save_improvement_opportunity(self, opportunity: ImprovementOpportunity) -> ImprovementOpportunity:
        stmt = select(ImprovementOpportunityModel).where(ImprovementOpportunityModel.id == opportunity.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = ImprovementOpportunityModel(id=opportunity.id)
            self.session.add(model)

        model.company_id = opportunity.company_id
        model.title = opportunity.title
        model.affected_area = opportunity.affected_area
        model.expected_impact = opportunity.expected_impact
        model.required_resources_json = json.dumps(opportunity.required_resources)
        model.risks_json = json.dumps(opportunity.risks)
        model.constraints_json = json.dumps(opportunity.constraints)
        model.confidence = opportunity.confidence
        model.identified_at = opportunity.identified_at

        await self.session.flush()
        return opportunity

    async def get_improvement_opportunity_by_id(self, opportunity_id: str) -> Optional[ImprovementOpportunity]:
        stmt = select(ImprovementOpportunityModel).where(ImprovementOpportunityModel.id == opportunity_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ImprovementOpportunity(
            id=m.id,
            company_id=m.company_id,
            title=m.title,
            affected_area=m.affected_area,
            expected_impact=m.expected_impact,
            required_resources=json.loads(m.required_resources_json) if m.required_resources_json else {},
            risks=json.loads(m.risks_json) if m.risks_json else [],
            constraints=json.loads(m.constraints_json) if m.constraints_json else [],
            confidence=m.confidence,
            identified_at=m.identified_at,
        )

    async def list_improvement_opportunities_for_company(self, company_id: str) -> List[ImprovementOpportunity]:
        stmt = select(ImprovementOpportunityModel).where(ImprovementOpportunityModel.company_id == company_id).order_by(ImprovementOpportunityModel.identified_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ImprovementOpportunity(
                id=m.id,
                company_id=m.company_id,
                title=m.title,
                affected_area=m.affected_area,
                expected_impact=m.expected_impact,
                required_resources=json.loads(m.required_resources_json) if m.required_resources_json else {},
                risks=json.loads(m.risks_json) if m.risks_json else [],
                constraints=json.loads(m.constraints_json) if m.constraints_json else [],
                confidence=m.confidence,
                identified_at=m.identified_at,
            )
            for m in models
        ]

    # 9. Adaptation Proposal
    async def save_adaptation_proposal(self, proposal: AdaptationProposal) -> AdaptationProposal:
        stmt = select(AdaptationProposalModel).where(AdaptationProposalModel.id == proposal.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = AdaptationProposalModel(id=proposal.id)
            self.session.add(model)

        model.company_id = proposal.company_id
        model.opportunity_id = proposal.opportunity_id
        model.adaptation_type = proposal.adaptation_type.value if isinstance(proposal.adaptation_type, Enum) else proposal.adaptation_type
        model.risk_level = proposal.risk_level.value if isinstance(proposal.risk_level, Enum) else proposal.risk_level
        model.current_state_json = json.dumps(proposal.current_state)
        model.proposed_state_json = json.dumps(proposal.proposed_state)
        model.rationale = proposal.rationale
        model.rollback_plan_json = json.dumps(proposal.rollback_plan)
        model.status = proposal.status.value if isinstance(proposal.status, Enum) else proposal.status
        model.governance_required = proposal.governance_required
        model.governance_approval_id = proposal.governance_approval_id
        model.updated_at = datetime.now(UTC)

        await self.session.flush()
        return proposal

    async def get_adaptation_proposal_by_id(self, proposal_id: str) -> Optional[AdaptationProposal]:
        stmt = select(AdaptationProposalModel).where(AdaptationProposalModel.id == proposal_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return AdaptationProposal(
            id=m.id,
            company_id=m.company_id,
            opportunity_id=m.opportunity_id,
            adaptation_type=AdaptationType(m.adaptation_type),
            risk_level=AdaptationRiskLevel(m.risk_level),
            current_state=json.loads(m.current_state_json) if m.current_state_json else {},
            proposed_state=json.loads(m.proposed_state_json) if m.proposed_state_json else {},
            rationale=m.rationale,
            rollback_plan=json.loads(m.rollback_plan_json) if m.rollback_plan_json else {},
            status=AdaptationStatus(m.status),
            governance_required=m.governance_required,
            governance_approval_id=m.governance_approval_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def list_adaptation_proposals_for_company(self, company_id: str) -> List[AdaptationProposal]:
        stmt = select(AdaptationProposalModel).where(AdaptationProposalModel.company_id == company_id).order_by(AdaptationProposalModel.created_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            AdaptationProposal(
                id=m.id,
                company_id=m.company_id,
                opportunity_id=m.opportunity_id,
                adaptation_type=AdaptationType(m.adaptation_type),
                risk_level=AdaptationRiskLevel(m.risk_level),
                current_state=json.loads(m.current_state_json) if m.current_state_json else {},
                proposed_state=json.loads(m.proposed_state_json) if m.proposed_state_json else {},
                rationale=m.rationale,
                rollback_plan=json.loads(m.rollback_plan_json) if m.rollback_plan_json else {},
                status=AdaptationStatus(m.status),
                governance_required=m.governance_required,
                governance_approval_id=m.governance_approval_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # 10. Adaptation Evaluation
    async def save_adaptation_evaluation(self, evaluation: AdaptationEvaluation) -> AdaptationEvaluation:
        stmt = select(AdaptationEvaluationModel).where(AdaptationEvaluationModel.id == evaluation.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = AdaptationEvaluationModel(id=evaluation.id)
            self.session.add(model)

        model.proposal_id = evaluation.proposal_id
        model.company_id = evaluation.company_id
        model.expected_benefit_score = evaluation.expected_benefit_score
        model.risk_score = evaluation.risk_score
        model.cost_score = evaluation.cost_score
        model.reversibility_score = evaluation.reversibility_score
        model.overall_recommendation_score = evaluation.overall_recommendation_score
        model.evaluation_breakdown_json = json.dumps(evaluation.evaluation_breakdown)
        model.evaluated_at = evaluation.evaluated_at

        await self.session.flush()
        return evaluation

    async def get_adaptation_evaluation_by_proposal_id(self, proposal_id: str) -> Optional[AdaptationEvaluation]:
        stmt = select(AdaptationEvaluationModel).where(AdaptationEvaluationModel.proposal_id == proposal_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return AdaptationEvaluation(
            id=m.id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            expected_benefit_score=m.expected_benefit_score,
            risk_score=m.risk_score,
            cost_score=m.cost_score,
            reversibility_score=m.reversibility_score,
            overall_recommendation_score=m.overall_recommendation_score,
            evaluation_breakdown=json.loads(m.evaluation_breakdown_json) if m.evaluation_breakdown_json else {},
            evaluated_at=m.evaluated_at,
        )

    # 11. Adaptation Execution
    async def save_adaptation_execution(self, execution: AdaptationExecution) -> AdaptationExecution:
        stmt = select(AdaptationExecutionModel).where(AdaptationExecutionModel.id == execution.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = AdaptationExecutionModel(id=execution.id)
            self.session.add(model)

        model.proposal_id = execution.proposal_id
        model.company_id = execution.company_id
        model.governance_approval_id = execution.governance_approval_id
        model.execution_type = execution.execution_type
        model.target_subsystem = execution.target_subsystem
        model.execution_payload_json = json.dumps(execution.execution_payload)
        model.dispatched_at = execution.dispatched_at
        model.completed_at = execution.completed_at

        await self.session.flush()
        return execution

    async def get_adaptation_execution_by_id(self, execution_id: str) -> Optional[AdaptationExecution]:
        stmt = select(AdaptationExecutionModel).where(AdaptationExecutionModel.id == execution_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return AdaptationExecution(
            id=m.id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            governance_approval_id=m.governance_approval_id,
            execution_type=m.execution_type,
            target_subsystem=m.target_subsystem,
            execution_payload=json.loads(m.execution_payload_json) if m.execution_payload_json else {},
            dispatched_at=m.dispatched_at,
            completed_at=m.completed_at,
        )

    # 12. Adaptation Outcome
    async def save_adaptation_outcome(self, outcome: AdaptationOutcome) -> AdaptationOutcome:
        stmt = select(AdaptationOutcomeModel).where(AdaptationOutcomeModel.id == outcome.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = AdaptationOutcomeModel(id=outcome.id)
            self.session.add(model)

        model.execution_id = outcome.execution_id
        model.proposal_id = outcome.proposal_id
        model.company_id = outcome.company_id
        model.expected_metrics_json = json.dumps(outcome.expected_metrics)
        model.actual_metrics_json = json.dumps(outcome.actual_metrics)
        model.variance_analysis_json = json.dumps(outcome.variance_analysis)
        model.side_effects_detected_json = json.dumps(outcome.side_effects_detected)
        model.has_regression = outcome.has_regression
        model.measured_at = outcome.measured_at

        await self.session.flush()
        return outcome

    async def get_adaptation_outcome_by_proposal_id(self, proposal_id: str) -> Optional[AdaptationOutcome]:
        stmt = select(AdaptationOutcomeModel).where(AdaptationOutcomeModel.proposal_id == proposal_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return AdaptationOutcome(
            id=m.id,
            execution_id=m.execution_id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            expected_metrics=json.loads(m.expected_metrics_json) if m.expected_metrics_json else {},
            actual_metrics=json.loads(m.actual_metrics_json) if m.actual_metrics_json else {},
            variance_analysis=json.loads(m.variance_analysis_json) if m.variance_analysis_json else {},
            side_effects_detected=json.loads(m.side_effects_detected_json) if m.side_effects_detected_json else [],
            has_regression=m.has_regression,
            measured_at=m.measured_at,
        )

    # 13. Adaptation Impact Assessment
    async def save_adaptation_impact_assessment(self, assessment: AdaptationImpactAssessment) -> AdaptationImpactAssessment:
        stmt = select(AdaptationImpactAssessmentModel).where(AdaptationImpactAssessmentModel.id == assessment.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = AdaptationImpactAssessmentModel(id=assessment.id)
            self.session.add(model)

        model.proposal_id = assessment.proposal_id
        model.company_id = assessment.company_id
        model.affected_subsystems_json = json.dumps(assessment.affected_subsystems)
        model.downstream_dependencies_json = json.dumps(assessment.downstream_dependencies)
        model.rollback_feasibility_score = assessment.rollback_feasibility_score
        model.assessed_at = assessment.assessed_at

        await self.session.flush()
        return assessment

    async def get_adaptation_impact_assessment_by_proposal_id(self, proposal_id: str) -> Optional[AdaptationImpactAssessment]:
        stmt = select(AdaptationImpactAssessmentModel).where(AdaptationImpactAssessmentModel.proposal_id == proposal_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return AdaptationImpactAssessment(
            id=m.id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            affected_subsystems=json.loads(m.affected_subsystems_json) if m.affected_subsystems_json else [],
            downstream_dependencies=json.loads(m.downstream_dependencies_json) if m.downstream_dependencies_json else [],
            rollback_feasibility_score=m.rollback_feasibility_score,
            assessed_at=m.assessed_at,
        )
