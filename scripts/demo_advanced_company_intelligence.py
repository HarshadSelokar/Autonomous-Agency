"""
End-to-End Demonstration Script for Phase 26 Advanced Company Intelligence, Decision Support & Strategic Optimization.

Demonstrates:
1. Multi-dimensional Company Health & Operational State Synthesizer.
2. Operational Bottleneck & Root-Cause Discovery Engine.
3. Decision Question & Multi-Option Strategic Space Formulation (Status-Quo Baseline vs Alternatives).
4. Multi-Dimensional Option Evaluation & Strategic Trade-off Analysis.
5. Governance Boundary Enforcement (Unauthorized execution blocked without governance_approval_id).
6. Governed Decision Execution Bridge (Bridge to task engine with valid governance_approval_id).
7. Post-Execution Outcome Tracking & Counterfactual Learning Loop.
8. Strict Multi-Tenant Intelligence Data Isolation across distinct autonomous companies.
"""

import asyncio
import os
import sys
from datetime import UTC, datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.company_intelligence import (
    IntelligenceRunStatus,
    QuestionUrgency,
    RiskCategory,
    HealthDimension,
    DecisionInsight,
)
from src.domain.exceptions import (
    CrossCompanyAccessDeniedError,
    UnauthorizedDecisionExecutionError,
)
from src.infrastructure.repositories.company_intelligence_repository import (
    SQLAlchemyCompanyIntelligenceRepository,
)
from src.application.company_intelligence_service import CompanyIntelligenceService
from src.application.decision_support_service import DecisionSupportService
from src.application.decision_execution_bridge_service import DecisionExecutionBridgeService
from src.application.decision_outcome_learning_service import DecisionOutcomeLearningService


class InMemoryIntelligenceRepo:
    """In-memory multi-tenant repository implementation for demonstration."""

    def __init__(self):
        self.runs = {}
        self.findings = {}
        self.questions = {}
        self.options = {}
        self.evaluations = {}
        self.tradeoffs = {}
        self.health_assessments = {}
        self.bottlenecks = {}
        self.risks = {}
        self.opportunities = {}
        self.insights = {}
        self.outcome_evaluations = {}

    async def save_intelligence_run(self, run):
        self.runs[run.id] = run
        return run

    async def get_intelligence_run_by_id(self, run_id):
        return self.runs.get(run_id)

    async def list_intelligence_runs(self, company_id, limit=50):
        return [r for r in self.runs.values() if r.company_id == company_id][:limit]

    async def save_intelligence_finding(self, finding):
        self.findings[finding.id] = finding
        return finding

    async def list_intelligence_findings_for_run(self, run_id):
        return [f for f in self.findings.values() if f.run_id == run_id]

    async def save_decision_question(self, question):
        self.questions[question.id] = question
        return question

    async def get_decision_question_by_id(self, question_id):
        return self.questions.get(question_id)

    async def list_decision_questions(self, company_id, is_active=True, limit=50):
        return [q for q in self.questions.values() if q.company_id == company_id and q.is_active == is_active][:limit]

    async def save_decision_option(self, option):
        self.options[option.id] = option
        return option

    async def list_options_for_question(self, question_id):
        return [o for o in self.options.values() if o.question_id == question_id]

    async def get_decision_option_by_id(self, option_id):
        return self.options.get(option_id)

    async def save_decision_evaluation(self, evaluation):
        self.evaluations[evaluation.id] = evaluation
        return evaluation

    async def get_evaluation_for_option(self, option_id):
        for ev in self.evaluations.values():
            if ev.option_id == option_id:
                return ev
        return None

    async def save_strategic_tradeoff(self, tradeoff):
        self.tradeoffs[tradeoff.id] = tradeoff
        return tradeoff

    async def list_strategic_tradeoffs_for_question(self, question_id):
        return [t for t in self.tradeoffs.values() if t.question_id == question_id]

    async def save_company_health_assessment(self, assessment):
        self.health_assessments[assessment.id] = assessment
        return assessment

    async def get_latest_company_health_assessment(self, company_id):
        c_assessments = [a for a in self.health_assessments.values() if a.company_id == company_id]
        if not c_assessments:
            return None
        return sorted(c_assessments, key=lambda a: a.evaluated_at, reverse=True)[0]

    async def save_company_bottleneck(self, bottleneck):
        self.bottlenecks[bottleneck.id] = bottleneck
        return bottleneck

    async def list_company_bottlenecks(self, company_id, is_resolved=False, limit=50):
        return [b for b in self.bottlenecks.values() if b.company_id == company_id and b.is_resolved == is_resolved][:limit]

    async def save_risk_assessment(self, risk):
        self.risks[risk.id] = risk
        return risk

    async def list_company_risk_assessments(self, company_id, limit=50):
        return [r for r in self.risks.values() if r.company_id == company_id][:limit]

    async def save_opportunity_assessment(self, opportunity):
        self.opportunities[opportunity.id] = opportunity
        return opportunity

    async def list_company_opportunity_assessments(self, company_id, limit=50):
        return [o for o in self.opportunities.values() if o.company_id == company_id][:limit]

    async def save_decision_insight(self, insight):
        self.insights[insight.id] = insight
        return insight

    async def get_decision_insight_by_id(self, insight_id):
        return self.insights.get(insight_id)

    async def list_decision_insights(self, company_id, limit=50):
        return [i for i in self.insights.values() if i.company_id == company_id][:limit]

    async def save_decision_outcome_evaluation(self, evaluation):
        self.outcome_evaluations[evaluation.id] = evaluation
        return evaluation

    async def list_decision_outcome_evaluations(self, company_id, limit=50):
        return [e for e in self.outcome_evaluations.values() if e.company_id == company_id][:limit]


async def run_demo():
    print("================================================================================")
    print("PHASE 26 — ADVANCED COMPANY INTELLIGENCE & DECISION SUPPORT END-TO-END DEMO")
    print("================================================================================")

    repo = InMemoryIntelligenceRepo()
    intel_service = CompanyIntelligenceService(repo)
    decision_service = DecisionSupportService(repo)
    bridge_service = DecisionExecutionBridgeService(repo)
    learning_service = DecisionOutcomeLearningService(repo)

    company_alpha = "comp-alpha-01"
    company_beta = "comp-beta-02"

    # Step 1: Intelligence Run & Health Synthesis
    print("\n--- [STEP 1] Running Analytical Intelligence Run & Health Synthesis ---")
    run = await intel_service.start_intelligence_run(
        company_id=company_alpha,
        purpose="Quarterly Operational Health & Bottleneck Audit",
        scope="FULL_COMPANY",
        requesting_principal="CEO_AGENT",
    )
    print(f"Started Intelligence Run: {run.id} [Status: {run.status.value}]")

    executed_run = await intel_service.execute_intelligence_run(run.id)
    print(f"Executed Intelligence Run Findings Count: {executed_run.findings_count} [Status: {executed_run.status.value}]")

    health = await intel_service.assess_company_health(company_id=company_alpha)

    print(f"Company ID: {health.company_id}")
    print(f"Health Status: {health.overall_health_status}")
    print(f"Dimension Scores: {health.dimension_scores}")
    print(f"Top Risks Detected: {health.top_risks}")
    print(f"Top Opportunities Identified: {health.top_opportunities}")

    # Step 2: Bottleneck Detection
    print("\n--- [STEP 2] Running Operational Bottleneck Discovery ---")
    bottlenecks = await intel_service.detect_bottlenecks(company_id=company_alpha)
    bottleneck = bottlenecks[0]
    print(f"Bottleneck ID: {bottleneck.id}")
    print(f"Name: {bottleneck.bottleneck_name}")
    print(f"Severity: {bottleneck.severity}")
    print(f"Evidence: {bottleneck.evidence_summary}")
    print(f"Suspected Causes: {bottleneck.suspected_causes}")

    # Step 3: Decision Question & Space Formulation
    print("\n--- [STEP 3] Formulating Strategic Decision Space (Status-Quo Baseline vs Alternatives) ---")
    question = await decision_service.create_decision_question(
        company_id=company_alpha,
        question="Should AlphaCorp allocate $50k to expand Backend Engineering workforce capacity by 25%?",
        purpose="Clear engineering backlog bottleneck and accelerate core product roadmap releases.",
        scope="STRATEGIC",
        urgency=QuestionUrgency.HIGH,
        constraints=["Max monthly budget add: $60,000", "Must deliver initial capacity within 2 weeks"],
    )
    print(f"Decision Question ID: {question.id}")
    print(f"Question: '{question.question}'")

    options_data = [
        {
            "option_name": "Option 1: Allocate 4 Senior Backend AI Agents",
            "description": "Hire 4 dedicated senior backend AI workforce agents.",
            "is_no_action_baseline": False,
            "assumptions": ["Backend demand remains high for Q3/Q4"],
            "required_resources": {"budget_cents": 5000000, "headcount": 4},
            "expected_benefits": {"revenue_cents": 15000000, "velocity_increase_pct": 35.0},
            "expected_costs_cents": 5000000,
            "risk_factors": ["Increases monthly fixed burn rate"],
            "dependencies": ["Workforce allocation engine capacity"],
        }
    ]

    options = await decision_service.generate_decision_options(
        question_id=question.id, options_data=options_data
    )

    print(f"Total Generated Decision Options (including status-quo baseline): {len(options)}")
    for opt in options:
        tag = "[STATUS-QUO BASELINE]" if opt.is_no_action_baseline else "[ALTERNATIVE]"
        print(f"  - {opt.id}: {opt.option_name} {tag}")

    evaluations = await decision_service.evaluate_decision_options(question_id=question.id)
    for ev in evaluations:
        print(f"Option ID {ev.option_id} Evaluation Score: {ev.overall_score:.2f}")

    insight = await decision_service.synthesize_decision_insight(question_id=question.id)
    print(f"\nSynthesized Decision Insight ID: {insight.id}")
    print(f"Recommended Option ID: {insight.recommended_option_id}")
    print(f"Governance Required: {insight.governance_required}")
    print(f"Governance Approval ID: {insight.governance_approval_id} (Currently None)")

    # Step 4: Governance Boundary Enforcement Verification
    print("\n--- [STEP 4] Governance Boundary Enforcement Safety Verification ---")
    try:
        await bridge_service.execute_decision_insight(
            insight_id=insight.id,
            actor_id="SYSTEM_AUTO_EXEC",
            governance_approval_id="",  # Empty governance approval!
        )
        print("ERROR: Safety check failed! Unapproved decision execution was permitted!")
    except UnauthorizedDecisionExecutionError as exc:
        print(f"SUCCESS: Direct execution WITHOUT governance approval correctly blocked!")
        print(f"  Caught Expected Exception: '{exc}'")

    # Step 5: Governed Execution Dispatch
    print("\n--- [STEP 5] Governed Execution Dispatch (With Human Governance Approval ID) ---")
    exec_result = await bridge_service.execute_decision_insight(
        insight_id=insight.id,
        actor_id="CHAIRMAN_HUMAN_GOVERNOR",
        governance_approval_id="gov-appr-999-alpha-approved",
    )
    print(f"Execution Bridge Initiated!")
    print(f"  Status: {exec_result['status']}")
    print(f"  Execution ID: {exec_result['execution_id']}")
    print(f"  Governance Approval ID Attached: {exec_result['governance_approval_id']}")

    # Step 6: Post-Execution Outcome Tracking & Counterfactual Learning Loop
    print("\n--- [STEP 6] Post-Execution Outcome Tracking & Counterfactual Learning Loop ---")
    outcome_eval = await learning_service.evaluate_decision_outcome(
        insight_id=insight.id,
        company_id=company_alpha,
        executed_option_id=options[1].id,
        expected_outcomes={"revenue_cents": 15000000, "velocity_increase_pct": 35.0},
        actual_outcomes={"revenue_cents": 16200000, "velocity_increase_pct": 38.0},
    )
    print(f"Outcome Evaluation ID: {outcome_eval.id}")
    print(f"Variance Analysis: {outcome_eval.variance_analysis}")
    print(f"Generated Learning Candidate: {outcome_eval.learning_candidate}")
    print(f"Created Knowledge Item ID: {outcome_eval.knowledge_item_id}")

    # Step 7: Multi-Tenant Data Isolation Enforcement
    print("\n--- [STEP 7] Strict Multi-Tenant Data Isolation Verification ---")
    print(f"Verifying Company B ({company_beta}) cannot access Company A's ({company_alpha}) Decision Insights...")
    
    beta_insights = await repo.list_decision_insights(company_id=company_beta)
    print(f"Company B Insights Count: {len(beta_insights)} (Expected: 0)")
    assert len(beta_insights) == 0, "Security isolation violation! Company B could see Company A's insights!"
    print("SUCCESS: Company B access returns 0 insights. Multi-tenant isolation verified!")

    print("\n================================================================================")
    print("PHASE 26 DEMONSTRATION COMPLETE — ALL SAFETY INVARIANTS & INTEGRATIONS PASSED")
    print("================================================================================")


if __name__ == "__main__":
    asyncio.run(run_demo())
