"""Unit tests for Phase 19 Research & Innovation Domain Entities."""

import pytest
from src.domain.research import (
    HypothesisStatus,
    InnovationProposal,
    InnovationType,
    OpportunityStatus,
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


def test_research_program_creation():
    prog = ResearchProgram(
        title="Autonomous Code Performance Optimization Program",
        purpose="Investigate LLM code optimization patterns",
        scope=ResearchScope.COMPANY,
    )
    assert prog.id.startswith("prog-")
    assert prog.status == "ACTIVE"
    assert prog.scope == ResearchScope.COMPANY


def test_research_request_and_question_hierarchy():
    req = ResearchRequest(
        question="How can read query latency be reduced by 50%?",
        purpose="Scale company database performance",
        scope=ResearchScope.TECHNOLOGY,
    )
    assert req.id.startswith("req-")
    assert req.governance_required is False

    q_main = ResearchQuestion(
        request_id=req.id,
        question="What database indexing techniques optimize JSONB queries?",
        scope=ResearchScope.TECHNOLOGY,
    )
    q_sub = ResearchQuestion(
        request_id=req.id,
        question="How does GIN index compare to BTREE on JSONB?",
        parent_question_id=q_main.id,
        scope=ResearchScope.TECHNOLOGY,
    )
    q_main.sub_question_ids.append(q_sub.id)

    assert q_main.id.startswith("q-")
    assert q_sub.parent_question_id == q_main.id
    assert len(q_main.sub_question_ids) == 1


def test_untrusted_source_and_hypothesis_invariants():
    source = ResearchSource(
        location="https://external-blog.com/tips",
        source_type=SourceType.APPROVED_EXTERNAL_WEBSITE,
        is_external=True,
    )
    # External content MUST be untrusted by default!
    assert source.is_untrusted is True

    hyp = ResearchHypothesis(
        observation="JSONB queries lag without index",
        statement="GIN index on payload column improves query time by 5x",
        prediction="Latency drops from 200ms to 40ms",
        status=HypothesisStatus.PROPOSED,
    )
    assert hyp.status == HypothesisStatus.PROPOSED

    hyp.update_status(HypothesisStatus.TESTING)
    assert hyp.status == HypothesisStatus.TESTING


def test_innovation_proposal_lifecycle():
    opp = ResearchOpportunity(
        title="Automated GIN Indexing Opportunity",
        description="Auto-generate GIN indexes for JSONB columns",
        status=OpportunityStatus.IDENTIFIED,
    )
    inno = InnovationProposal(
        opportunity_id=opp.id,
        title="Autonomous GIN Index Generator",
        innovation_type=InnovationType.TECHNOLOGY_INNOVATION,
        problem_statement="Unindexed JSONB columns cause high DB load",
        proposed_solution="Autonomous index suggestion engine",
        reversibility="HIGH",
    )
    assert inno.id.startswith("inno-")
    assert inno.is_approved is False
    assert inno.strategic_initiative_id is None
