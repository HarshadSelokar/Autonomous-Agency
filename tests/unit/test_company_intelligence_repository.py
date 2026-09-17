"""
Unit tests for SQLAlchemyCompanyIntelligenceRepository.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.company_intelligence import (
    IntelligenceRun,
    IntelligenceRunStatus,
    DecisionQuestion,
    DecisionOption,
    DecisionEvaluation,
    DecisionInsight,
    CompanyHealthAssessment,
    CompanyBottleneck,
    CompanyRiskAssessment,
    DecisionOutcomeEvaluation,
)
from src.infrastructure.database import Base
import src.infrastructure.models.company_intelligence_model
from src.infrastructure.repositories.company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository


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
async def test_intelligence_run_repository_flow(async_session: AsyncSession):
    repo = SQLAlchemyCompanyIntelligenceRepository(async_session)

    run = IntelligenceRun(company_id="comp-intel-1", purpose="Q4 Capacity Audit")
    saved = await repo.save_intelligence_run(run)
    assert saved.id == run.id

    fetched = await repo.get_intelligence_run_by_id(run.id)
    assert fetched is not None
    assert fetched.purpose == "Q4 Capacity Audit"

    runs_list = await repo.list_intelligence_runs_for_company("comp-intel-1")
    assert len(runs_list) == 1
    assert runs_list[0].id == run.id


@pytest.mark.asyncio
async def test_decision_question_option_insight_repository_flow(async_session: AsyncSession):
    repo = SQLAlchemyCompanyIntelligenceRepository(async_session)

    # Question
    q = DecisionQuestion(company_id="comp-intel-1", question="Should pricing increase 15%?")
    saved_q = await repo.save_decision_question(q)
    assert saved_q.id == q.id

    # Options
    opt0 = DecisionOption(question_id=q.id, company_id="comp-intel-1", option_name="No Action", is_no_action_baseline=True)
    opt1 = DecisionOption(question_id=q.id, company_id="comp-intel-1", option_name="15% Price Hike", expected_costs_cents=0)
    await repo.save_decision_option(opt0)
    await repo.save_decision_option(opt1)

    opts = await repo.list_options_for_question(q.id)
    assert len(opts) == 2

    # Insight
    insight = DecisionInsight(
        question_id=q.id,
        company_id="comp-intel-1",
        recommendation_summary="Proceed with 15% price hike",
        recommended_option_id=opt1.id,
    )
    saved_insight = await repo.save_decision_insight(insight)
    assert saved_insight.id == insight.id

    fetched_insight = await repo.get_decision_insight_by_question_id(q.id)
    assert fetched_insight is not None
    assert fetched_insight.recommended_option_id == opt1.id


@pytest.mark.asyncio
async def test_company_health_and_bottleneck_repository(async_session: AsyncSession):
    repo = SQLAlchemyCompanyIntelligenceRepository(async_session)

    health = CompanyHealthAssessment(
        company_id="comp-intel-1",
        overall_health_status="HEALTHY",
        dimension_scores={"strategic": 0.9, "financial": 0.85},
    )
    await repo.save_company_health_assessment(health)

    fetched_health = await repo.get_latest_health_assessment_for_company("comp-intel-1")
    assert fetched_health is not None
    assert fetched_health.dimension_scores["strategic"] == 0.9

    bn = CompanyBottleneck(
        company_id="comp-intel-1",
        bottleneck_name="Task Queue Backlog",
        affected_scope="ENGINEERING",
        severity="HIGH",
    )
    await repo.save_company_bottleneck(bn)

    bns = await repo.list_active_bottlenecks_for_company("comp-intel-1")
    assert len(bns) == 1
    assert bns[0].bottleneck_name == "Task Queue Backlog"
