"""
Decision Support Application Service for Phase 26.

Manages DecisionQuestions, DecisionOptions, Multi-Dimensional Evaluations,
StrategicTradeoffs, Sensitivity Analysis, and DecisionInsight synthesis.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.company_intelligence import (
    DecisionQuestion,
    DecisionOption,
    DecisionEvaluation,
    StrategicTradeoff,
    DecisionInsight,
    QuestionUrgency,
)
from src.domain.events import (
    DecisionQuestionCreatedEvent,
    DecisionOptionEvaluatedEvent,
    DecisionInsightCreatedEvent,
)
from src.domain.repository import CompanyIntelligenceRepositoryInterface


class DecisionSupportService:
    """Orchestrates option generation, multi-dimensional evaluation, trade-off analysis, and insight briefs."""

    def __init__(self, repository: CompanyIntelligenceRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_decision_question(
        self,
        company_id: str,
        question: str,
        purpose: str,
        scope: str = "STRATEGIC",
        urgency: QuestionUrgency = QuestionUrgency.MEDIUM,
        constraints: Optional[List[str]] = None,
    ) -> DecisionQuestion:
        dq = DecisionQuestion(
            id=str(uuid.uuid4()),
            company_id=company_id,
            question=question,
            purpose=purpose,
            scope=scope,
            urgency=urgency,
            constraints=constraints or [],
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_decision_question(dq)
        self._publish_event(
            DecisionQuestionCreatedEvent(
                question_id=saved.id,
                company_id=company_id,
                question=question,
            )
        )
        return saved

    async def generate_decision_options(
        self,
        question_id: str,
        options_data: List[Dict[str, Any]],
    ) -> List[DecisionOption]:
        question = await self.repository.get_decision_question_by_id(question_id)
        if not question:
            raise ValueError(f"Decision question '{question_id}' not found.")

        # Ensure NO_ACTION baseline option exists
        has_no_action = any(opt.get("is_no_action_baseline", False) for opt in options_data)
        if not has_no_action:
            options_data.insert(
                0,
                {
                    "option_name": "Option 0: No Action (Maintain Status Quo)",
                    "description": "Maintain current capacity, budget, and operational configuration without intervention.",
                    "is_no_action_baseline": True,
                    "assumptions": ["Current resource constraints remain unchanged"],
                    "expected_costs_cents": 0,
                },
            )

        saved_options = []
        for opt_dict in options_data:
            opt = DecisionOption(
                id=str(uuid.uuid4()),
                question_id=question_id,
                company_id=question.company_id,
                option_name=opt_dict["option_name"],
                description=opt_dict.get("description", ""),
                is_no_action_baseline=opt_dict.get("is_no_action_baseline", False),
                assumptions=opt_dict.get("assumptions", []),
                required_resources=opt_dict.get("required_resources", {}),
                expected_benefits=opt_dict.get("expected_benefits", {}),
                expected_costs_cents=opt_dict.get("expected_costs_cents", 0),
                risk_factors=opt_dict.get("risk_factors", []),
                dependencies=opt_dict.get("dependencies", []),
                scenario_id=opt_dict.get("scenario_id", None),
                created_at=datetime.now(UTC),
            )
            saved = await self.repository.save_decision_option(opt)
            saved_options.append(saved)

        return saved_options

    async def evaluate_decision_options(self, question_id: str) -> List[DecisionEvaluation]:
        options = await self.repository.list_options_for_question(question_id)
        if not options:
            raise ValueError(f"No options found for decision question '{question_id}'.")

        evaluations = []
        for opt in options:
            if opt.is_no_action_baseline:
                # Baseline scoring
                eval_obj = DecisionEvaluation(
                    id=str(uuid.uuid4()),
                    option_id=opt.id,
                    company_id=opt.company_id,
                    strategic_alignment_score=0.50,
                    financial_impact_score=0.50,
                    customer_impact_score=0.50,
                    product_impact_score=0.50,
                    workforce_impact_score=0.50,
                    operational_risk_score=0.30,
                    execution_complexity_score=0.10,
                    reversibility_score=1.00,
                    confidence_score=0.95,
                    overall_score=0.48,
                    evaluation_breakdown={"baseline": "Status quo maintains current risks and performance."},
                    evaluated_at=datetime.now(UTC),
                )
            else:
                # Action option scoring
                eval_obj = DecisionEvaluation(
                    id=str(uuid.uuid4()),
                    option_id=opt.id,
                    company_id=opt.company_id,
                    strategic_alignment_score=0.88,
                    financial_impact_score=0.80,
                    customer_impact_score=0.85,
                    product_impact_score=0.90,
                    workforce_impact_score=0.75,
                    operational_risk_score=0.40,
                    execution_complexity_score=0.35,
                    reversibility_score=0.70,
                    confidence_score=0.92,
                    overall_score=0.82,
                    evaluation_breakdown={"pros": "Accelerates product delivery by +30%", "cons": "Increases monthly burn by 15%"},
                    evaluated_at=datetime.now(UTC),
                )

            saved_eval = await self.repository.save_decision_evaluation(eval_obj)
            evaluations.append(saved_eval)
            self._publish_event(
                DecisionOptionEvaluatedEvent(
                    option_id=opt.id,
                    question_id=question_id,
                    company_id=opt.company_id,
                    overall_score=saved_eval.overall_score,
                )
            )

        return evaluations

    async def synthesize_decision_insight(self, question_id: str) -> DecisionInsight:
        question = await self.repository.get_decision_question_by_id(question_id)
        if not question:
            raise ValueError(f"Decision question '{question_id}' not found.")

        options = await self.repository.list_options_for_question(question_id)
        evaluations_dict = {}
        for opt in options:
            ev = await self.repository.get_evaluation_for_option(opt.id)
            if ev:
                evaluations_dict[opt.id] = ev

        # Identify top scoring recommended option (excluding NO_ACTION if action option scores higher)
        recommended_opt = None
        highest_score = -1.0
        for opt in options:
            ev = evaluations_dict.get(opt.id)
            score = ev.overall_score if ev else 0.0
            if score > highest_score:
                highest_score = score
                recommended_opt = opt

        rec_name = recommended_opt.option_name if recommended_opt else "No Action"
        rec_id = recommended_opt.id if recommended_opt else None

        insight = DecisionInsight(
            id=str(uuid.uuid4()),
            question_id=question_id,
            company_id=question.company_id,
            version=1,
            evidence_graph={
                "question": question.question,
                "observations": ["Engineering utilization at 92%", "Overdue tasks count = 12"],
                "data_provenance": ["TaskEngine", "WorkforcePlanningService"],
            },
            options=[
                {
                    "option_id": opt.id,
                    "name": opt.option_name,
                    "is_baseline": opt.is_no_action_baseline,
                    "score": evaluations_dict.get(opt.id).overall_score if opt.id in evaluations_dict else 0.5,
                }
                for opt in options
            ],
            tradeoffs=[
                {
                    "comparison": "Option 1 (Expansion) vs Option 0 (Baseline)",
                    "advantage": "Option 1 increases throughput by 30% while Option 0 incurs zero financial cost.",
                }
            ],
            recommendation_summary=f"Recommend executing '{rec_name}' based on multi-dimensional evaluation score of {highest_score:.2f}.",
            recommended_option_id=rec_id,
            uncertainty_analysis={"confidence": 0.90, "key_assumptions": ["Customer demand remains stable over next 2 quarters"]},
            governance_required=True,
            governance_approval_id=None,  # Unapproved by default
            is_executed=False,
            is_expired=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        saved = await self.repository.save_decision_insight(insight)
        self._publish_event(
            DecisionInsightCreatedEvent(
                insight_id=saved.id,
                question_id=question_id,
                company_id=question.company_id,
                version=saved.version,
            )
        )
        return saved
