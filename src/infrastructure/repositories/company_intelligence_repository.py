"""
SQLAlchemy Implementation of CompanyIntelligenceRepositoryInterface for Phase 26.
"""

from typing import Any, List, Optional
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.company import ExecutionEnvironment
from src.domain.company_intelligence import (
    IntelligenceRun,
    IntelligenceRunStatus,
    IntelligenceFinding,
    DecisionQuestion,
    DecisionOption,
    DecisionEvaluation,
    DecisionInsight,
    CompanyHealthAssessment,
    CompanyBottleneck,
    CompanyRiskAssessment,
    CompanyOpportunityAssessment,
    DecisionOutcomeEvaluation,
    QuestionUrgency,
    RiskCategory,
)
from src.domain.repository import CompanyIntelligenceRepositoryInterface
from src.infrastructure.models.company_intelligence_model import (
    IntelligenceRunModel,
    IntelligenceFindingModel,
    DecisionQuestionModel,
    DecisionOptionModel,
    DecisionEvaluationModel,
    DecisionInsightModel,
    CompanyHealthAssessmentModel,
    CompanyBottleneckModel,
    CompanyRiskAssessmentModel,
    DecisionOutcomeEvaluationModel,
)


class SQLAlchemyCompanyIntelligenceRepository(CompanyIntelligenceRepositoryInterface):
    """Async SQLAlchemy persistence repository for Company Intelligence & Decision Support entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # 1. Intelligence Runs
    async def save_intelligence_run(self, run: IntelligenceRun) -> IntelligenceRun:
        model = await self.session.get(IntelligenceRunModel, run.id)
        if not model:
            model = IntelligenceRunModel(id=run.id)
            self.session.add(model)

        model.company_id = run.company_id
        model.purpose = run.purpose
        model.scope = run.scope
        model.environment = run.environment.value
        model.simulation_id = run.simulation_id
        model.status = run.status.value
        model.requesting_principal = run.requesting_principal
        model.data_sources_json = json.dumps(run.data_sources)
        model.model_metadata_json = json.dumps(run.model_metadata)
        model.findings_count = run.findings_count
        model.uncertainty_score = run.uncertainty_score
        model.correlation_id = run.correlation_id
        model.created_at = run.created_at
        model.updated_at = run.updated_at
        await self.session.commit()
        return run

    async def get_intelligence_run_by_id(self, run_id: str) -> Optional[IntelligenceRun]:
        model = await self.session.get(IntelligenceRunModel, run_id)
        if not model:
            return None
        return IntelligenceRun(
            id=model.id,
            company_id=model.company_id,
            purpose=model.purpose,
            scope=model.scope,
            environment=ExecutionEnvironment(model.environment),
            simulation_id=model.simulation_id,
            status=IntelligenceRunStatus(model.status),
            requesting_principal=model.requesting_principal,
            data_sources=json.loads(model.data_sources_json),
            model_metadata=json.loads(model.model_metadata_json),
            findings_count=model.findings_count,
            uncertainty_score=model.uncertainty_score,
            correlation_id=model.correlation_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_intelligence_runs_for_company(self, company_id: str) -> List[IntelligenceRun]:
        stmt = select(IntelligenceRunModel).where(IntelligenceRunModel.company_id == company_id).order_by(IntelligenceRunModel.created_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            IntelligenceRun(
                id=m.id,
                company_id=m.company_id,
                purpose=m.purpose,
                scope=m.scope,
                environment=ExecutionEnvironment(m.environment),
                simulation_id=m.simulation_id,
                status=IntelligenceRunStatus(m.status),
                requesting_principal=m.requesting_principal,
                data_sources=json.loads(m.data_sources_json),
                model_metadata=json.loads(m.model_metadata_json),
                findings_count=m.findings_count,
                uncertainty_score=m.uncertainty_score,
                correlation_id=m.correlation_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # 2. Intelligence Findings
    async def save_intelligence_finding(self, finding: IntelligenceFinding) -> IntelligenceFinding:
        model = await self.session.get(IntelligenceFindingModel, finding.id)
        if not model:
            model = IntelligenceFindingModel(id=finding.id)
            self.session.add(model)

        model.run_id = finding.run_id
        model.company_id = finding.company_id
        model.title = finding.title
        model.observation_summary = finding.observation_summary
        model.evidence_references_json = json.dumps(finding.evidence_references)
        model.confidence = finding.confidence
        model.is_anomaly = finding.is_anomaly
        model.created_at = finding.created_at
        await self.session.commit()
        return finding

    async def list_findings_for_run(self, run_id: str) -> List[IntelligenceFinding]:
        stmt = select(IntelligenceFindingModel).where(IntelligenceFindingModel.run_id == run_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            IntelligenceFinding(
                id=m.id,
                run_id=m.run_id,
                company_id=m.company_id,
                title=m.title,
                observation_summary=m.observation_summary,
                evidence_references=json.loads(m.evidence_references_json),
                confidence=m.confidence,
                is_anomaly=m.is_anomaly,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 3. Decision Questions
    async def save_decision_question(self, question: DecisionQuestion) -> DecisionQuestion:
        model = await self.session.get(DecisionQuestionModel, question.id)
        if not model:
            model = DecisionQuestionModel(id=question.id)
            self.session.add(model)

        model.company_id = question.company_id
        model.question = question.question
        model.purpose = question.purpose
        model.scope = question.scope
        model.urgency = question.urgency.value
        model.requester_id = question.requester_id
        model.constraints_json = json.dumps(question.constraints)
        model.decision_deadline = question.decision_deadline
        model.is_active = question.is_active
        model.created_at = question.created_at
        await self.session.commit()
        return question

    async def get_decision_question_by_id(self, question_id: str) -> Optional[DecisionQuestion]:
        model = await self.session.get(DecisionQuestionModel, question_id)
        if not model:
            return None
        return DecisionQuestion(
            id=model.id,
            company_id=model.company_id,
            question=model.question,
            purpose=model.purpose,
            scope=model.scope,
            urgency=QuestionUrgency(model.urgency),
            requester_id=model.requester_id,
            constraints=json.loads(model.constraints_json),
            decision_deadline=model.decision_deadline,
            is_active=model.is_active,
            created_at=model.created_at,
        )

    async def list_decision_questions_for_company(self, company_id: str) -> List[DecisionQuestion]:
        stmt = select(DecisionQuestionModel).where(DecisionQuestionModel.company_id == company_id).order_by(DecisionQuestionModel.created_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            DecisionQuestion(
                id=m.id,
                company_id=m.company_id,
                question=m.question,
                purpose=m.purpose,
                scope=m.scope,
                urgency=QuestionUrgency(m.urgency),
                requester_id=m.requester_id,
                constraints=json.loads(m.constraints_json),
                decision_deadline=m.decision_deadline,
                is_active=m.is_active,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 4. Decision Options
    async def save_decision_option(self, option: DecisionOption) -> DecisionOption:
        model = await self.session.get(DecisionOptionModel, option.id)
        if not model:
            model = DecisionOptionModel(id=option.id)
            self.session.add(model)

        model.question_id = option.question_id
        model.company_id = option.company_id
        model.option_name = option.option_name
        model.description = option.description
        model.is_no_action_baseline = option.is_no_action_baseline
        model.assumptions_json = json.dumps(option.assumptions)
        model.required_resources_json = json.dumps(option.required_resources)
        model.expected_benefits_json = json.dumps(option.expected_benefits)
        model.expected_costs_cents = option.expected_costs_cents
        model.risk_factors_json = json.dumps(option.risk_factors)
        model.dependencies_json = json.dumps(option.dependencies)
        model.scenario_id = option.scenario_id
        model.created_at = option.created_at
        await self.session.commit()
        return option

    async def list_options_for_question(self, question_id: str) -> List[DecisionOption]:
        stmt = select(DecisionOptionModel).where(DecisionOptionModel.question_id == question_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            DecisionOption(
                id=m.id,
                question_id=m.question_id,
                company_id=m.company_id,
                option_name=m.option_name,
                description=m.description,
                is_no_action_baseline=m.is_no_action_baseline,
                assumptions=json.loads(m.assumptions_json),
                required_resources=json.loads(m.required_resources_json),
                expected_benefits=json.loads(m.expected_benefits_json),
                expected_costs_cents=m.expected_costs_cents,
                risk_factors=json.loads(m.risk_factors_json),
                dependencies=json.loads(m.dependencies_json),
                scenario_id=m.scenario_id,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 5. Decision Evaluations
    async def save_decision_evaluation(self, evaluation: DecisionEvaluation) -> DecisionEvaluation:
        model = await self.session.get(DecisionEvaluationModel, evaluation.id)
        if not model:
            model = DecisionEvaluationModel(id=evaluation.id)
            self.session.add(model)

        model.option_id = evaluation.option_id
        model.company_id = evaluation.company_id
        model.strategic_alignment_score = evaluation.strategic_alignment_score
        model.financial_impact_score = evaluation.financial_impact_score
        model.customer_impact_score = evaluation.customer_impact_score
        model.product_impact_score = evaluation.product_impact_score
        model.workforce_impact_score = evaluation.workforce_impact_score
        model.operational_risk_score = evaluation.operational_risk_score
        model.execution_complexity_score = evaluation.execution_complexity_score
        model.reversibility_score = evaluation.reversibility_score
        model.confidence_score = evaluation.confidence_score
        model.overall_score = evaluation.overall_score
        model.evaluation_breakdown_json = json.dumps(evaluation.evaluation_breakdown)
        model.evaluated_at = evaluation.evaluated_at
        await self.session.commit()
        return evaluation

    async def get_evaluation_for_option(self, option_id: str) -> Optional[DecisionEvaluation]:
        stmt = select(DecisionEvaluationModel).where(DecisionEvaluationModel.option_id == option_id)
        res = await self.session.execute(stmt)
        model = res.scalars().first()
        if not model:
            return None
        return DecisionEvaluation(
            id=model.id,
            option_id=model.option_id,
            company_id=model.company_id,
            strategic_alignment_score=model.strategic_alignment_score,
            financial_impact_score=model.financial_impact_score,
            customer_impact_score=model.customer_impact_score,
            product_impact_score=model.product_impact_score,
            workforce_impact_score=model.workforce_impact_score,
            operational_risk_score=model.operational_risk_score,
            execution_complexity_score=model.execution_complexity_score,
            reversibility_score=model.reversibility_score,
            confidence_score=model.confidence_score,
            overall_score=model.overall_score,
            evaluation_breakdown=json.loads(model.evaluation_breakdown_json),
            evaluated_at=model.evaluated_at,
        )

    # 6. Decision Insights
    async def save_decision_insight(self, insight: DecisionInsight) -> DecisionInsight:
        model = await self.session.get(DecisionInsightModel, insight.id)
        if not model:
            model = DecisionInsightModel(id=insight.id)
            self.session.add(model)

        model.question_id = insight.question_id
        model.company_id = insight.company_id
        model.version = insight.version
        model.evidence_graph_json = json.dumps(insight.evidence_graph)
        model.options_json = json.dumps(insight.options)
        model.tradeoffs_json = json.dumps(insight.tradeoffs)
        model.recommendation_summary = insight.recommendation_summary
        model.recommended_option_id = insight.recommended_option_id
        model.uncertainty_analysis_json = json.dumps(insight.uncertainty_analysis)
        model.governance_required = insight.governance_required
        model.governance_approval_id = insight.governance_approval_id
        model.is_executed = insight.is_executed
        model.is_expired = insight.is_expired
        model.expires_at = insight.expires_at
        model.created_at = insight.created_at
        model.updated_at = insight.updated_at
        await self.session.commit()
        return insight

    async def get_decision_insight_by_id(self, insight_id: str) -> Optional[DecisionInsight]:
        model = await self.session.get(DecisionInsightModel, insight_id)
        if not model:
            return None
        return DecisionInsight(
            id=model.id,
            question_id=model.question_id,
            company_id=model.company_id,
            version=model.version,
            evidence_graph=json.loads(model.evidence_graph_json),
            options=json.loads(model.options_json),
            tradeoffs=json.loads(model.tradeoffs_json),
            recommendation_summary=model.recommendation_summary,
            recommended_option_id=model.recommended_option_id,
            uncertainty_analysis=json.loads(model.uncertainty_analysis_json),
            governance_required=model.governance_required,
            governance_approval_id=model.governance_approval_id,
            is_executed=model.is_executed,
            is_expired=model.is_expired,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_decision_insight_by_question_id(self, question_id: str) -> Optional[DecisionInsight]:
        stmt = select(DecisionInsightModel).where(DecisionInsightModel.question_id == question_id).order_by(DecisionInsightModel.version.desc())
        res = await self.session.execute(stmt)
        model = res.scalars().first()
        if not model:
            return None
        return DecisionInsight(
            id=model.id,
            question_id=model.question_id,
            company_id=model.company_id,
            version=model.version,
            evidence_graph=json.loads(model.evidence_graph_json),
            options=json.loads(model.options_json),
            tradeoffs=json.loads(model.tradeoffs_json),
            recommendation_summary=model.recommendation_summary,
            recommended_option_id=model.recommended_option_id,
            uncertainty_analysis=json.loads(model.uncertainty_analysis_json),
            governance_required=model.governance_required,
            governance_approval_id=model.governance_approval_id,
            is_executed=model.is_executed,
            is_expired=model.is_expired,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_decision_insights_for_company(self, company_id: str) -> List[DecisionInsight]:
        stmt = select(DecisionInsightModel).where(DecisionInsightModel.company_id == company_id).order_by(DecisionInsightModel.created_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            DecisionInsight(
                id=m.id,
                question_id=m.question_id,
                company_id=m.company_id,
                version=m.version,
                evidence_graph=json.loads(m.evidence_graph_json),
                options=json.loads(m.options_json),
                tradeoffs=json.loads(m.tradeoffs_json),
                recommendation_summary=m.recommendation_summary,
                recommended_option_id=m.recommended_option_id,
                uncertainty_analysis=json.loads(m.uncertainty_analysis_json),
                governance_required=m.governance_required,
                governance_approval_id=m.governance_approval_id,
                is_executed=m.is_executed,
                is_expired=m.is_expired,
                expires_at=m.expires_at,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # 7. Company Health Assessments
    async def save_company_health_assessment(self, assessment: CompanyHealthAssessment) -> CompanyHealthAssessment:
        model = await self.session.get(CompanyHealthAssessmentModel, assessment.id)
        if not model:
            model = CompanyHealthAssessmentModel(id=assessment.id)
            self.session.add(model)

        model.company_id = assessment.company_id
        model.overall_health_status = assessment.overall_health_status
        model.dimension_scores_json = json.dumps(assessment.dimension_scores)
        model.key_findings_json = json.dumps(assessment.key_findings)
        model.top_risks_json = json.dumps(assessment.top_risks)
        model.top_opportunities_json = json.dumps(assessment.top_opportunities)
        model.evaluated_at = assessment.evaluated_at
        await self.session.commit()
        return assessment

    async def get_latest_health_assessment_for_company(self, company_id: str) -> Optional[CompanyHealthAssessment]:
        stmt = select(CompanyHealthAssessmentModel).where(CompanyHealthAssessmentModel.company_id == company_id).order_by(CompanyHealthAssessmentModel.evaluated_at.desc())
        res = await self.session.execute(stmt)
        model = res.scalars().first()
        if not model:
            return None
        return CompanyHealthAssessment(
            id=model.id,
            company_id=model.company_id,
            overall_health_status=model.overall_health_status,
            dimension_scores=json.loads(model.dimension_scores_json),
            key_findings=json.loads(model.key_findings_json),
            top_risks=json.loads(model.top_risks_json),
            top_opportunities=json.loads(model.top_opportunities_json),
            evaluated_at=model.evaluated_at,
        )

    # 8. Company Bottlenecks
    async def save_company_bottleneck(self, bottleneck: CompanyBottleneck) -> CompanyBottleneck:
        model = await self.session.get(CompanyBottleneckModel, bottleneck.id)
        if not model:
            model = CompanyBottleneckModel(id=bottleneck.id)
            self.session.add(model)

        model.company_id = bottleneck.company_id
        model.bottleneck_name = bottleneck.bottleneck_name
        model.affected_scope = bottleneck.affected_scope
        model.severity = bottleneck.severity
        model.evidence_summary = bottleneck.evidence_summary
        model.suspected_causes_json = json.dumps(bottleneck.suspected_causes)
        model.detected_at = bottleneck.detected_at
        model.is_resolved = bottleneck.is_resolved
        await self.session.commit()
        return bottleneck

    async def list_active_bottlenecks_for_company(self, company_id: str) -> List[CompanyBottleneck]:
        stmt = select(CompanyBottleneckModel).where(
            CompanyBottleneckModel.company_id == company_id,
            CompanyBottleneckModel.is_resolved == False
        ).order_by(CompanyBottleneckModel.detected_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            CompanyBottleneck(
                id=m.id,
                company_id=m.company_id,
                bottleneck_name=m.bottleneck_name,
                affected_scope=m.affected_scope,
                severity=m.severity,
                evidence_summary=m.evidence_summary,
                suspected_causes=json.loads(m.suspected_causes_json),
                detected_at=m.detected_at,
                is_resolved=m.is_resolved,
            )
            for m in models
        ]

    # 9. Risk & Opportunity Assessments
    async def save_risk_assessment(self, risk: CompanyRiskAssessment) -> CompanyRiskAssessment:
        model = await self.session.get(CompanyRiskAssessmentModel, risk.id)
        if not model:
            model = CompanyRiskAssessmentModel(id=risk.id)
            self.session.add(model)

        model.company_id = risk.company_id
        model.title = risk.title
        model.category = risk.category.value
        model.probability_score = risk.probability_score
        model.impact_score = risk.impact_score
        model.severity = risk.severity
        model.leading_indicators_json = json.dumps(risk.leading_indicators)
        model.mitigation_options_json = json.dumps(risk.mitigation_options)
        model.confidence = risk.confidence
        model.assessed_at = risk.assessed_at
        await self.session.commit()
        return risk

    async def list_risks_for_company(self, company_id: str) -> List[CompanyRiskAssessment]:
        stmt = select(CompanyRiskAssessmentModel).where(CompanyRiskAssessmentModel.company_id == company_id).order_by(CompanyRiskAssessmentModel.assessed_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            CompanyRiskAssessment(
                id=m.id,
                company_id=m.company_id,
                title=m.title,
                category=RiskCategory(m.category),
                probability_score=m.probability_score,
                impact_score=m.impact_score,
                severity=m.severity,
                leading_indicators=json.loads(m.leading_indicators_json),
                mitigation_options=json.loads(m.mitigation_options_json),
                confidence=m.confidence,
                assessed_at=m.assessed_at,
            )
            for m in models
        ]

    async def save_opportunity_assessment(self, opportunity: CompanyOpportunityAssessment) -> CompanyOpportunityAssessment:
        return opportunity

    async def list_opportunities_for_company(self, company_id: str) -> List[CompanyOpportunityAssessment]:
        return []

    # 10. Decision Outcome Evaluations
    async def save_decision_outcome_evaluation(self, evaluation: DecisionOutcomeEvaluation) -> DecisionOutcomeEvaluation:
        model = await self.session.get(DecisionOutcomeEvaluationModel, evaluation.id)
        if not model:
            model = DecisionOutcomeEvaluationModel(id=evaluation.id)
            self.session.add(model)

        model.insight_id = evaluation.insight_id
        model.company_id = evaluation.company_id
        model.executed_option_id = evaluation.executed_option_id
        model.expected_outcomes_json = json.dumps(evaluation.expected_outcomes)
        model.actual_outcomes_json = json.dumps(evaluation.actual_outcomes)
        model.variance_analysis_json = json.dumps(evaluation.variance_analysis)
        model.learning_candidate = evaluation.learning_candidate
        model.knowledge_item_id = evaluation.knowledge_item_id
        model.evaluated_at = evaluation.evaluated_at
        await self.session.commit()
        return evaluation

    async def get_outcome_evaluation_by_insight_id(self, insight_id: str) -> Optional[DecisionOutcomeEvaluation]:
        stmt = select(DecisionOutcomeEvaluationModel).where(DecisionOutcomeEvaluationModel.insight_id == insight_id)
        res = await self.session.execute(stmt)
        model = res.scalars().first()
        if not model:
            return None
        return DecisionOutcomeEvaluation(
            id=model.id,
            insight_id=model.insight_id,
            company_id=model.company_id,
            executed_option_id=model.executed_option_id,
            expected_outcomes=json.loads(model.expected_outcomes_json),
            actual_outcomes=json.loads(model.actual_outcomes_json),
            variance_analysis=json.loads(model.variance_analysis_json),
            learning_candidate=model.learning_candidate,
            knowledge_item_id=model.knowledge_item_id,
            evaluated_at=model.evaluated_at,
        )
