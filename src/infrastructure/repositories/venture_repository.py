"""
SQLAlchemy Implementation of VentureRepositoryInterface for Phase 28.
"""

import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.venture import (
    InnovationOpportunity,
    OpportunityStatus,
    InnovationIdea,
    BusinessHypothesis,
    HypothesisStatus,
    ProductConcept,
    BusinessModelConcept,
    VentureBusinessCase,
    BusinessCaseStatus,
    InnovationValidation,
    VentureExperiment,
    InnovationReview,
    VentureProposal,
    VentureType,
    ProposalStatus,
    VentureInitializationPlan,
    VentureResourceRequest,
    VentureLaunchReadiness,
    LaunchReadinessStatus,
    VentureOutcome,
    VentureOutcomeStatus,
)
from src.domain.repository import VentureRepositoryInterface
from src.infrastructure.models.venture_model import (
    InnovationOpportunityModel,
    InnovationIdeaModel,
    BusinessHypothesisModel,
    ProductConceptModel,
    BusinessModelConceptModel,
    VentureBusinessCaseModel,
    InnovationValidationModel,
    VentureExperimentModel,
    InnovationReviewModel,
    VentureProposalModel,
    VentureInitializationPlanModel,
    VentureResourceRequestModel,
    VentureLaunchReadinessModel,
    VentureOutcomeModel,
)


class SQLAlchemyVentureRepository(VentureRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # 1. Opportunity
    async def save_opportunity(self, opportunity: InnovationOpportunity) -> InnovationOpportunity:
        stmt = select(InnovationOpportunityModel).where(InnovationOpportunityModel.id == opportunity.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = InnovationOpportunityModel(id=opportunity.id)
            self.session.add(model)

        model.company_id = opportunity.company_id
        model.title = opportunity.title
        model.description = opportunity.description
        model.source = opportunity.source
        model.problem_statement = opportunity.problem_statement
        model.customer_need = opportunity.customer_need
        model.market_signal_json = json.dumps(opportunity.market_signal)
        model.evidence_json = json.dumps(opportunity.evidence)
        model.strategic_relevance = opportunity.strategic_relevance
        model.confidence = opportunity.confidence
        model.assumptions_json = json.dumps(opportunity.assumptions)
        model.risks_json = json.dumps(opportunity.risks)
        model.potential_impact = opportunity.potential_impact
        model.status = opportunity.status.value if isinstance(opportunity.status, Enum) else opportunity.status
        model.updated_at = datetime.now(UTC)

        await self.session.commit()
        return opportunity

    async def get_opportunity_by_id(self, opportunity_id: str) -> Optional[InnovationOpportunity]:
        stmt = select(InnovationOpportunityModel).where(InnovationOpportunityModel.id == opportunity_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return InnovationOpportunity(
            id=m.id,
            company_id=m.company_id,
            title=m.title,
            description=m.description,
            source=m.source,
            problem_statement=m.problem_statement,
            customer_need=m.customer_need,
            market_signal=json.loads(m.market_signal_json or "{}"),
            evidence=json.loads(m.evidence_json or "[]"),
            strategic_relevance=m.strategic_relevance,
            confidence=m.confidence,
            assumptions=json.loads(m.assumptions_json or "[]"),
            risks=json.loads(m.risks_json or "[]"),
            potential_impact=m.potential_impact,
            status=OpportunityStatus(m.status),
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def list_opportunities_for_company(self, company_id: str) -> List[InnovationOpportunity]:
        stmt = select(InnovationOpportunityModel).where(InnovationOpportunityModel.company_id == company_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            InnovationOpportunity(
                id=m.id,
                company_id=m.company_id,
                title=m.title,
                description=m.description,
                source=m.source,
                problem_statement=m.problem_statement,
                customer_need=m.customer_need,
                market_signal=json.loads(m.market_signal_json or "{}"),
                evidence=json.loads(m.evidence_json or "[]"),
                strategic_relevance=m.strategic_relevance,
                confidence=m.confidence,
                assumptions=json.loads(m.assumptions_json or "[]"),
                risks=json.loads(m.risks_json or "[]"),
                potential_impact=m.potential_impact,
                status=OpportunityStatus(m.status),
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # 2. Idea
    async def save_idea(self, idea: InnovationIdea) -> InnovationIdea:
        stmt = select(InnovationIdeaModel).where(InnovationIdeaModel.id == idea.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = InnovationIdeaModel(id=idea.id)
            self.session.add(model)

        model.opportunity_id = idea.opportunity_id
        model.company_id = idea.company_id
        model.title = idea.title
        model.description = idea.description
        model.proposed_solution = idea.proposed_solution
        model.target_customer = idea.target_customer
        model.value_proposition = idea.value_proposition
        model.differentiator = idea.differentiator
        model.assumptions_json = json.dumps(idea.assumptions)
        model.dependencies_json = json.dumps(idea.dependencies)
        model.risks_json = json.dumps(idea.risks)
        model.required_capabilities_json = json.dumps(idea.required_capabilities)

        await self.session.commit()
        return idea

    async def get_idea_by_id(self, idea_id: str) -> Optional[InnovationIdea]:
        stmt = select(InnovationIdeaModel).where(InnovationIdeaModel.id == idea_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return InnovationIdea(
            id=m.id,
            opportunity_id=m.opportunity_id,
            company_id=m.company_id,
            title=m.title,
            description=m.description,
            proposed_solution=m.proposed_solution,
            target_customer=m.target_customer,
            value_proposition=m.value_proposition,
            differentiator=m.differentiator,
            assumptions=json.loads(m.assumptions_json or "[]"),
            dependencies=json.loads(m.dependencies_json or "[]"),
            risks=json.loads(m.risks_json or "[]"),
            required_capabilities=json.loads(m.required_capabilities_json or "[]"),
            created_at=m.created_at,
        )

    async def list_ideas_for_company(self, company_id: str) -> List[InnovationIdea]:
        stmt = select(InnovationIdeaModel).where(InnovationIdeaModel.company_id == company_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            InnovationIdea(
                id=m.id,
                opportunity_id=m.opportunity_id,
                company_id=m.company_id,
                title=m.title,
                description=m.description,
                proposed_solution=m.proposed_solution,
                target_customer=m.target_customer,
                value_proposition=m.value_proposition,
                differentiator=m.differentiator,
                assumptions=json.loads(m.assumptions_json or "[]"),
                dependencies=json.loads(m.dependencies_json or "[]"),
                risks=json.loads(m.risks_json or "[]"),
                required_capabilities=json.loads(m.required_capabilities_json or "[]"),
                created_at=m.created_at,
            )
            for m in models
        ]

    # 3. Hypothesis
    async def save_hypothesis(self, hypothesis: BusinessHypothesis) -> BusinessHypothesis:
        stmt = select(BusinessHypothesisModel).where(BusinessHypothesisModel.id == hypothesis.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = BusinessHypothesisModel(id=hypothesis.id)
            self.session.add(model)

        model.idea_id = hypothesis.idea_id
        model.company_id = hypothesis.company_id
        model.assumption = hypothesis.assumption
        model.supporting_evidence_json = json.dumps(hypothesis.supporting_evidence)
        model.confidence = hypothesis.confidence
        model.validation_method = hypothesis.validation_method
        model.failure_condition = hypothesis.failure_condition
        model.status = hypothesis.status.value if isinstance(hypothesis.status, Enum) else hypothesis.status

        await self.session.commit()
        return hypothesis

    async def get_hypothesis_by_id(self, hypothesis_id: str) -> Optional[BusinessHypothesis]:
        stmt = select(BusinessHypothesisModel).where(BusinessHypothesisModel.id == hypothesis_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return BusinessHypothesis(
            id=m.id,
            idea_id=m.idea_id,
            company_id=m.company_id,
            assumption=m.assumption,
            supporting_evidence=json.loads(m.supporting_evidence_json or "[]"),
            confidence=m.confidence,
            validation_method=m.validation_method,
            failure_condition=m.failure_condition,
            status=HypothesisStatus(m.status),
            created_at=m.created_at,
        )

    async def list_hypotheses_for_company(self, company_id: str) -> List[BusinessHypothesis]:
        stmt = select(BusinessHypothesisModel).where(BusinessHypothesisModel.company_id == company_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            BusinessHypothesis(
                id=m.id,
                idea_id=m.idea_id,
                company_id=m.company_id,
                assumption=m.assumption,
                supporting_evidence=json.loads(m.supporting_evidence_json or "[]"),
                confidence=m.confidence,
                validation_method=m.validation_method,
                failure_condition=m.failure_condition,
                status=HypothesisStatus(m.status),
                created_at=m.created_at,
            )
            for m in models
        ]

    # 4. Product Concept
    async def save_product_concept(self, concept: ProductConcept) -> ProductConcept:
        stmt = select(ProductConceptModel).where(ProductConceptModel.id == concept.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = ProductConceptModel(id=concept.id)
            self.session.add(model)

        model.idea_id = concept.idea_id
        model.company_id = concept.company_id
        model.name = concept.name
        model.target_segment = concept.target_segment
        model.capabilities_json = json.dumps(concept.capabilities)
        model.value_proposition = concept.value_proposition
        model.pricing_hypothesis_json = json.dumps(concept.pricing_hypothesis)
        model.distribution_channel = concept.distribution_channel

        await self.session.commit()
        return concept

    async def get_product_concept_by_id(self, concept_id: str) -> Optional[ProductConcept]:
        stmt = select(ProductConceptModel).where(ProductConceptModel.id == concept_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ProductConcept(
            id=m.id,
            idea_id=m.idea_id,
            company_id=m.company_id,
            name=m.name,
            target_segment=m.target_segment,
            capabilities=json.loads(m.capabilities_json or "[]"),
            value_proposition=m.value_proposition,
            pricing_hypothesis=json.loads(m.pricing_hypothesis_json or "{}"),
            distribution_channel=m.distribution_channel,
            created_at=m.created_at,
        )

    # 5. Business Model Concept
    async def save_business_model_concept(self, concept: BusinessModelConcept) -> BusinessModelConcept:
        stmt = select(BusinessModelConceptModel).where(BusinessModelConceptModel.id == concept.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = BusinessModelConceptModel(id=concept.id)
            self.session.add(model)

        model.idea_id = concept.idea_id
        model.company_id = concept.company_id
        model.revenue_model = concept.revenue_model
        model.pricing_model_json = json.dumps(concept.pricing_model)
        model.acquisition_strategy = concept.acquisition_strategy
        model.cost_structure_json = json.dumps(concept.cost_structure)
        model.gross_margin_est = concept.gross_margin_est
        model.operating_model = concept.operating_model

        await self.session.commit()
        return concept

    async def get_business_model_concept_by_id(self, concept_id: str) -> Optional[BusinessModelConcept]:
        stmt = select(BusinessModelConceptModel).where(BusinessModelConceptModel.id == concept_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return BusinessModelConcept(
            id=m.id,
            idea_id=m.idea_id,
            company_id=m.company_id,
            revenue_model=m.revenue_model,
            pricing_model=json.loads(m.pricing_model_json or "{}"),
            acquisition_strategy=m.acquisition_strategy,
            cost_structure=json.loads(m.cost_structure_json or "{}"),
            gross_margin_est=m.gross_margin_est,
            operating_model=m.operating_model,
            created_at=m.created_at,
        )

    # 6. Venture Business Case
    async def save_business_case(self, business_case: VentureBusinessCase) -> VentureBusinessCase:
        stmt = select(VentureBusinessCaseModel).where(VentureBusinessCaseModel.id == business_case.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = VentureBusinessCaseModel(id=business_case.id)
            self.session.add(model)

        model.opportunity_id = business_case.opportunity_id
        model.company_id = business_case.company_id
        model.title = business_case.title
        model.market_assumptions_json = json.dumps(business_case.market_assumptions)
        model.financial_model_json = json.dumps(business_case.financial_model)
        model.workforce_reqs_json = json.dumps(business_case.workforce_reqs)
        model.infra_reqs_json = json.dumps(business_case.infra_reqs)
        model.risk_analysis_json = json.dumps(business_case.risk_analysis)
        model.scenarios_json = json.dumps(business_case.scenarios)
        model.expected_roi = business_case.expected_roi
        model.uncertainty_score = business_case.uncertainty_score
        model.status = business_case.status.value if isinstance(business_case.status, Enum) else business_case.status
        model.updated_at = datetime.now(UTC)

        await self.session.commit()
        return business_case

    async def get_business_case_by_id(self, business_case_id: str) -> Optional[VentureBusinessCase]:
        stmt = select(VentureBusinessCaseModel).where(VentureBusinessCaseModel.id == business_case_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return VentureBusinessCase(
            id=m.id,
            opportunity_id=m.opportunity_id,
            company_id=m.company_id,
            title=m.title,
            market_assumptions=json.loads(m.market_assumptions_json or "{}"),
            financial_model=json.loads(m.financial_model_json or "{}"),
            workforce_reqs=json.loads(m.workforce_reqs_json or "{}"),
            infra_reqs=json.loads(m.infra_reqs_json or "{}"),
            risk_analysis=json.loads(m.risk_analysis_json or "{}"),
            scenarios=json.loads(m.scenarios_json or "{}"),
            expected_roi=m.expected_roi,
            uncertainty_score=m.uncertainty_score,
            status=BusinessCaseStatus(m.status),
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def list_business_cases_for_company(self, company_id: str) -> List[VentureBusinessCase]:
        stmt = select(VentureBusinessCaseModel).where(VentureBusinessCaseModel.company_id == company_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            VentureBusinessCase(
                id=m.id,
                opportunity_id=m.opportunity_id,
                company_id=m.company_id,
                title=m.title,
                market_assumptions=json.loads(m.market_assumptions_json or "{}"),
                financial_model=json.loads(m.financial_model_json or "{}"),
                workforce_reqs=json.loads(m.workforce_reqs_json or "{}"),
                infra_reqs=json.loads(m.infra_reqs_json or "{}"),
                risk_analysis=json.loads(m.risk_analysis_json or "{}"),
                scenarios=json.loads(m.scenarios_json or "{}"),
                expected_roi=m.expected_roi,
                uncertainty_score=m.uncertainty_score,
                status=BusinessCaseStatus(m.status),
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # 7. Validation
    async def save_validation(self, validation: InnovationValidation) -> InnovationValidation:
        stmt = select(InnovationValidationModel).where(InnovationValidationModel.id == validation.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = InnovationValidationModel(id=validation.id)
            self.session.add(model)

        model.opportunity_id = validation.opportunity_id
        model.company_id = validation.company_id
        model.validation_method = validation.validation_method
        model.evidence_summary = validation.evidence_summary
        model.confidence_score = validation.confidence_score
        model.unresolved_assumptions_json = json.dumps(validation.unresolved_assumptions)

        await self.session.commit()
        return validation

    async def get_validation_by_id(self, validation_id: str) -> Optional[InnovationValidation]:
        stmt = select(InnovationValidationModel).where(InnovationValidationModel.id == validation_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return InnovationValidation(
            id=m.id,
            opportunity_id=m.opportunity_id,
            company_id=m.company_id,
            validation_method=m.validation_method,
            evidence_summary=m.evidence_summary,
            confidence_score=m.confidence_score,
            unresolved_assumptions=json.loads(m.unresolved_assumptions_json or "[]"),
            validated_at=m.validated_at,
        )

    # 8. Experiment
    async def save_experiment(self, experiment: VentureExperiment) -> VentureExperiment:
        stmt = select(VentureExperimentModel).where(VentureExperimentModel.id == experiment.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = VentureExperimentModel(id=experiment.id)
            self.session.add(model)

        model.proposal_id = experiment.proposal_id
        model.company_id = experiment.company_id
        model.hypothesis = experiment.hypothesis
        model.control_config_json = json.dumps(experiment.control_config)
        model.treatment_config_json = json.dumps(experiment.treatment_config)
        model.duration_days = experiment.duration_days
        model.metrics_json = json.dumps(experiment.metrics)
        model.success_criteria_json = json.dumps(experiment.success_criteria)
        model.status = experiment.status

        await self.session.commit()
        return experiment

    async def get_experiment_by_id(self, experiment_id: str) -> Optional[VentureExperiment]:
        stmt = select(VentureExperimentModel).where(VentureExperimentModel.id == experiment_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return VentureExperiment(
            id=m.id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            hypothesis=m.hypothesis,
            control_config=json.loads(m.control_config_json or "{}"),
            treatment_config=json.loads(m.treatment_config_json or "{}"),
            duration_days=m.duration_days,
            metrics=json.loads(m.metrics_json or "{}"),
            success_criteria=json.loads(m.success_criteria_json or "{}"),
            status=m.status,
            created_at=m.created_at,
        )

    # 9. Review
    async def save_review(self, review: InnovationReview) -> InnovationReview:
        stmt = select(InnovationReviewModel).where(InnovationReviewModel.id == review.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = InnovationReviewModel(id=review.id)
            self.session.add(model)

        model.proposal_id = review.proposal_id
        model.company_id = review.company_id
        model.strategic_fit_score = review.strategic_fit_score
        model.customer_value_score = review.customer_value_score
        model.technical_feasibility_score = review.technical_feasibility_score
        model.economic_viability_score = review.economic_viability_score
        model.risk_score = review.risk_score
        model.overall_score = review.overall_score
        model.recommendation = review.recommendation

        await self.session.commit()
        return review

    async def get_review_by_id(self, review_id: str) -> Optional[InnovationReview]:
        stmt = select(InnovationReviewModel).where(InnovationReviewModel.id == review_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return InnovationReview(
            id=m.id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            strategic_fit_score=m.strategic_fit_score,
            customer_value_score=m.customer_value_score,
            technical_feasibility_score=m.technical_feasibility_score,
            economic_viability_score=m.economic_viability_score,
            risk_score=m.risk_score,
            overall_score=m.overall_score,
            recommendation=m.recommendation,
            reviewed_at=m.reviewed_at,
        )

    # 10. Proposal
    async def save_proposal(self, proposal: VentureProposal) -> VentureProposal:
        stmt = select(VentureProposalModel).where(VentureProposalModel.id == proposal.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = VentureProposalModel(id=proposal.id)
            self.session.add(model)

        model.opportunity_id = proposal.opportunity_id
        model.company_id = proposal.company_id
        model.title = proposal.title
        model.venture_type = proposal.venture_type.value if isinstance(proposal.venture_type, Enum) else proposal.venture_type
        model.business_case_id = proposal.business_case_id
        model.required_budget_usd = proposal.required_budget_usd
        model.required_workforce_count = proposal.required_workforce_count
        model.risk_level = proposal.risk_level
        model.status = proposal.status.value if isinstance(proposal.status, Enum) else proposal.status
        model.governance_required = proposal.governance_required
        model.governance_approval_id = proposal.governance_approval_id
        model.updated_at = datetime.now(UTC)

        await self.session.commit()
        return proposal

    async def get_proposal_by_id(self, proposal_id: str) -> Optional[VentureProposal]:
        stmt = select(VentureProposalModel).where(VentureProposalModel.id == proposal_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return VentureProposal(
            id=m.id,
            opportunity_id=m.opportunity_id,
            company_id=m.company_id,
            title=m.title,
            venture_type=VentureType(m.venture_type),
            business_case_id=m.business_case_id,
            required_budget_usd=m.required_budget_usd,
            required_workforce_count=m.required_workforce_count,
            risk_level=m.risk_level,
            status=ProposalStatus(m.status),
            governance_required=m.governance_required,
            governance_approval_id=m.governance_approval_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def list_proposals_for_company(self, company_id: str) -> List[VentureProposal]:
        stmt = select(VentureProposalModel).where(VentureProposalModel.company_id == company_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            VentureProposal(
                id=m.id,
                opportunity_id=m.opportunity_id,
                company_id=m.company_id,
                title=m.title,
                venture_type=VentureType(m.venture_type),
                business_case_id=m.business_case_id,
                required_budget_usd=m.required_budget_usd,
                required_workforce_count=m.required_workforce_count,
                risk_level=m.risk_level,
                status=ProposalStatus(m.status),
                governance_required=m.governance_required,
                governance_approval_id=m.governance_approval_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # 11. Initialization Plan
    async def save_initialization_plan(self, plan: VentureInitializationPlan) -> VentureInitializationPlan:
        stmt = select(VentureInitializationPlanModel).where(VentureInitializationPlanModel.id == plan.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = VentureInitializationPlanModel(id=plan.id)
            self.session.add(model)

        model.proposal_id = plan.proposal_id
        model.company_id = plan.company_id
        model.target_structure = plan.target_structure.value if isinstance(plan.target_structure, Enum) else plan.target_structure
        model.departments_json = json.dumps(plan.departments)
        model.workforce_plan_json = json.dumps(plan.workforce_plan)
        model.product_config_json = json.dumps(plan.product_config)
        model.financial_setup_json = json.dumps(plan.financial_setup)

        await self.session.commit()
        return plan

    async def get_initialization_plan_by_id(self, plan_id: str) -> Optional[VentureInitializationPlan]:
        stmt = select(VentureInitializationPlanModel).where(VentureInitializationPlanModel.id == plan_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return VentureInitializationPlan(
            id=m.id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            target_structure=VentureType(m.target_structure),
            departments=json.loads(m.departments_json or "[]"),
            workforce_plan=json.loads(m.workforce_plan_json or "{}"),
            product_config=json.loads(m.product_config_json or "{}"),
            financial_setup=json.loads(m.financial_setup_json or "{}"),
            created_at=m.created_at,
        )

    # 12. Resource Request
    async def save_resource_request(self, request: VentureResourceRequest) -> VentureResourceRequest:
        stmt = select(VentureResourceRequestModel).where(VentureResourceRequestModel.id == request.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = VentureResourceRequestModel(id=request.id)
            self.session.add(model)

        model.proposal_id = request.proposal_id
        model.company_id = request.company_id
        model.workforce_count = request.workforce_count
        model.model_budget_usd = request.model_budget_usd
        model.storage_gb = request.storage_gb
        model.compute_cores = request.compute_cores
        model.status = request.status

        await self.session.commit()
        return request

    # 13. Launch Readiness
    async def save_launch_readiness(self, readiness: VentureLaunchReadiness) -> VentureLaunchReadiness:
        stmt = select(VentureLaunchReadinessModel).where(VentureLaunchReadinessModel.id == readiness.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = VentureLaunchReadinessModel(id=readiness.id)
            self.session.add(model)

        model.proposal_id = readiness.proposal_id
        model.company_id = readiness.company_id
        model.product_ready = readiness.product_ready
        model.technical_ready = readiness.technical_ready
        model.security_ready = readiness.security_ready
        model.financial_ready = readiness.financial_ready
        model.governance_ready = readiness.governance_ready
        model.status = readiness.status.value if isinstance(readiness.status, Enum) else readiness.status

        await self.session.commit()
        return readiness

    async def get_launch_readiness_by_proposal_id(self, proposal_id: str) -> Optional[VentureLaunchReadiness]:
        stmt = select(VentureLaunchReadinessModel).where(VentureLaunchReadinessModel.proposal_id == proposal_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return VentureLaunchReadiness(
            id=m.id,
            proposal_id=m.proposal_id,
            company_id=m.company_id,
            product_ready=m.product_ready,
            technical_ready=m.technical_ready,
            security_ready=m.security_ready,
            financial_ready=m.financial_ready,
            governance_ready=m.governance_ready,
            status=LaunchReadinessStatus(m.status),
            checked_at=m.checked_at,
        )

    # 14. Outcome
    async def save_outcome(self, outcome: VentureOutcome) -> VentureOutcome:
        stmt = select(VentureOutcomeModel).where(VentureOutcomeModel.id == outcome.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = VentureOutcomeModel(id=outcome.id)
            self.session.add(model)

        model.venture_id = outcome.venture_id
        model.company_id = outcome.company_id
        model.expected_outcomes_json = json.dumps(outcome.expected_outcomes)
        model.actual_outcomes_json = json.dumps(outcome.actual_outcomes)
        model.variance_analysis_json = json.dumps(outcome.variance_analysis)
        model.status = outcome.status.value if isinstance(outcome.status, Enum) else outcome.status

        await self.session.commit()
        return outcome

    async def get_outcome_by_id(self, outcome_id: str) -> Optional[VentureOutcome]:
        stmt = select(VentureOutcomeModel).where(VentureOutcomeModel.id == outcome_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return VentureOutcome(
            id=m.id,
            venture_id=m.venture_id,
            company_id=m.company_id,
            expected_outcomes=json.loads(m.expected_outcomes_json or "{}"),
            actual_outcomes=json.loads(m.actual_outcomes_json or "{}"),
            variance_analysis=json.loads(m.variance_analysis_json or "{}"),
            status=VentureOutcomeStatus(m.status),
            measured_at=m.measured_at,
        )
