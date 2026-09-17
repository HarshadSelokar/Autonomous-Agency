"""
Unit tests for Phase 26 Company Intelligence Application Services.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.company_intelligence import IntelligenceRunStatus, QuestionUrgency
from src.domain.exceptions import UnauthorizedDecisionExecutionError, DecisionInsightExpiredError
from src.infrastructure.database import Base
import src.infrastructure.models.company_intelligence_model
from src.infrastructure.repositories.company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
from src.application.company_intelligence_service import CompanyIntelligenceService
from src.application.decision_support_service import DecisionSupportService
from src.application.decision_execution_bridge_service import DecisionExecutionBridgeService
from src.application.decision_outcome_learning_service import DecisionOutcomeLearningService


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_company_intelligence_service_flow(async_session: AsyncSession):
    repo = SQLAlchemyCompanyIntelligenceRepository(async_session)
    intel_svc = CompanyIntelligenceService(repo)

    company_id = "comp-test-01"

    # 1. Start & Execute Intelligence Run
    run = await intel_svc.start_intelligence_run(company_id, "Monthly Intelligence Audit")
    assert run.status == IntelligenceRunStatus.REQUESTED

    executed_run = await intel_svc.execute_intelligence_run(run.id)
    assert executed_run.status == IntelligenceRunStatus.COMPLETED
    assert executed_run.findings_count == 2

    # 2. Assess Company Health
    health = await intel_svc.assess_company_health(company_id)
    assert health.overall_health_status == "BALANCED"
    assert "strategic" in health.dimension_scores

    # 3. Detect Bottlenecks & Risks
    bns = await intel_svc.detect_bottlenecks(company_id)
    assert len(bns) == 1
    assert bns[0].severity == "HIGH"

    risks = await intel_svc.assess_risks(company_id)
    assert len(risks) == 1
    assert risks[0].category.value == "WORKFORCE"


@pytest.mark.asyncio
async def test_decision_support_and_governance_bridge_flow(async_session: AsyncSession):
    repo = SQLAlchemyCompanyIntelligenceRepository(async_session)
    support_svc = DecisionSupportService(repo)
    bridge_svc = DecisionExecutionBridgeService(repo)

    company_id = "comp-test-01"

    # 1. Formulate Question
    q = await support_svc.create_decision_question(
        company_id=company_id,
        question="Should we expand Engineering team capacity by 25%?",
        purpose="Evaluate Q4 product delivery throughput",
        urgency=QuestionUrgency.HIGH,
    )

    # 2. Generate Options (includes NO_ACTION baseline)
    options = await support_svc.generate_decision_options(
        q.id,
        [
            {
                "option_name": "Option 1: Add 3 Senior Frontend Engineers",
                "description": "Increase team headcount to accelerate release velocity.",
                "expected_costs_cents": 4500000,
            }
        ],
    )
    assert len(options) == 2  # Baseline NO_ACTION + Option 1
    assert any(opt.is_no_action_baseline for opt in options)

    # 3. Evaluate Options
    evals = await support_svc.evaluate_decision_options(q.id)
    assert len(evals) == 2

    # 4. Synthesize Decision Insight
    insight = await support_svc.synthesize_decision_insight(q.id)
    assert insight.version == 1
    assert insight.governance_required is True

    # 5. Execution Bridge without governance approval -> raises UnauthorizedDecisionExecutionError
    with pytest.raises(UnauthorizedDecisionExecutionError):
        await bridge_svc.execute_decision_insight(insight.id, "actor-manager-1", governance_approval_id=None)

    # 6. Execution Bridge with governance approval -> succeeds
    exec_res = await bridge_svc.execute_decision_insight(insight.id, "actor-manager-1", governance_approval_id="gov-appr-999")
    assert exec_res["status"] == "GOVERNED_EXECUTION_INITIATED"
    assert exec_res["governance_approval_id"] == "gov-appr-999"


@pytest.mark.asyncio
async def test_decision_outcome_learning_service(async_session: AsyncSession):
    repo = SQLAlchemyCompanyIntelligenceRepository(async_session)
    learning_svc = DecisionOutcomeLearningService(repo)

    outcome = await learning_svc.evaluate_decision_outcome(
        insight_id="insight-999",
        company_id="comp-test-01",
        executed_option_id="opt-expand-1",
        expected_outcomes={"revenue_cents": 10000000},
        actual_outcomes={"revenue_cents": 11000000},
    )

    assert outcome.variance_analysis["revenue_variance_pct"] == 10.0
    assert outcome.variance_analysis["outcome_status"] == "SUCCESS"
    assert "ki-lesson-" in outcome.knowledge_item_id
