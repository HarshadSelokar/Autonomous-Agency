"""Integration tests for Phase 19 Research & Innovation Repository."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.research import (
    HypothesisStatus,
    InnovationProposal,
    InnovationType,
    OpportunityStatus,
    ResearchEvidence,
    ResearchFinding,
    ResearchHypothesis,
    ResearchOpportunity,
    ResearchProgram,
    ResearchQuestion,
    ResearchRequest,
    ResearchScope,
    ResearchSource,
    SourceType,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.research_repository import SQLAlchemyResearchRepository


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_research_program_and_request_persistence(db_session):
    repo = SQLAlchemyResearchRepository(db_session)

    prog = await repo.save_program(
        ResearchProgram(
            title="AI Architecture Evaluation",
            purpose="Assess new model routing benchmarks",
            scope=ResearchScope.TECHNOLOGY,
        )
    )
    fetched_prog = await repo.get_program_by_id(prog.id)
    assert fetched_prog is not None
    assert fetched_prog.title == "AI Architecture Evaluation"

    req = await repo.save_request(
        ResearchRequest(
            question="Can model routing latency be reduced by 30%?",
            purpose="Latency optimization",
            scope=ResearchScope.MODEL,
        )
    )
    fetched_req = await repo.get_request_by_id(req.id)
    assert fetched_req is not None
    assert fetched_req.question == req.question


@pytest.mark.asyncio
async def test_source_evidence_finding_hypothesis_persistence(db_session):
    repo = SQLAlchemyResearchRepository(db_session)

    src = await repo.save_source(
        ResearchSource(
            location="https://arxiv.org/abs/2401.00001",
            source_type=SourceType.PUBLIC_RESEARCH_PAPER,
            is_external=True,
            is_untrusted=True,
            reliability_score=0.88,
        )
    )
    assert src.is_untrusted is True

    ev = await repo.save_evidence(
        ResearchEvidence(
            source_id=src.id,
            content_snippet="Speculative decoding reduces latency by 2.5x",
            is_independent=True,
        )
    )

    q = await repo.save_question(
        ResearchQuestion(
            request_id="req-101",
            question="Does speculative decoding improve model throughput?",
        )
    )

    find = await repo.save_finding(
        ResearchFinding(
            question_id=q.id,
            finding_statement="Speculative decoding delivers 2.2x speedup on Groq infrastructure",
            evidence_ids=[ev.id],
            confidence=0.92,
        )
    )
    fetched_find = await repo.get_finding_by_id(find.id)
    assert fetched_find is not None
    assert fetched_find.confidence == 0.92

    hyp = await repo.save_hypothesis(
        ResearchHypothesis(
            question_id=q.id,
            observation="Groq inference latency drops with draft model",
            statement="Integrating draft model router decreases p99 latency",
            status=HypothesisStatus.TESTING,
        )
    )
    fetched_hyp = await repo.get_hypothesis_by_id(hyp.id)
    assert fetched_hyp is not None
    assert fetched_hyp.status == HypothesisStatus.TESTING


@pytest.mark.asyncio
async def test_opportunity_and_innovation_proposal_persistence(db_session):
    repo = SQLAlchemyResearchRepository(db_session)

    opp = await repo.save_opportunity(
        ResearchOpportunity(
            finding_id="find-999",
            title="Speculative Routing Service Opportunity",
            description="Build speculative routing adapter",
            status=OpportunityStatus.IDENTIFIED,
        )
    )

    prop = await repo.save_proposal(
        InnovationProposal(
            opportunity_id=opp.id,
            title="Autonomous Speculative Model Router",
            innovation_type=InnovationType.MODEL_ROUTING_INNOVATION,
            problem_statement="High latency on 70B parameter models",
            proposed_solution="Route draft tokens to 8B model",
            expected_value="30% token cost reduction & 2x speedup",
        )
    )
    fetched_prop = await repo.get_proposal_by_id(prop.id)
    assert fetched_prop is not None
    assert fetched_prop.title == "Autonomous Speculative Model Router"
    assert fetched_prop.is_approved is False
