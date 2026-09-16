"""Phase 19 Failure Injection Test Suite.

Verifies system resilience against:
1. Fake citations & unbacked research findings.
2. Derivative snippet duplicate detection (enforcing evidence independence).
3. Missing entities (requests, questions, opportunities, proposals).
4. Invalid/corrupted evidence data.
"""

import pytest
from unittest.mock import AsyncMock

from src.application.research_services import (
    InnovationEngineService,
    ResearchEvidenceService,
    ResearchHypothesisService,
    ResearchPlanningService,
)
from src.domain.research import ResearchEvidence, ResearchSource, SourceType


@pytest.mark.asyncio
async def test_fake_citation_unbacked_finding_injection():
    mock_repo = AsyncMock()
    ev_svc = ResearchEvidenceService(mock_repo)

    # Attempt to synthesize finding with NO evidence IDs
    with pytest.raises(ValueError, match="MUST reference at least 1 valid evidence item"):
        await ev_svc.synthesize_finding(
            question_id="q-fake-1",
            finding_statement="Fabricated claim without empirical evidence.",
            evidence_ids=[],
            confidence=0.99,
        )


@pytest.mark.asyncio
async def test_derivative_duplicate_content_detection():
    mock_repo = AsyncMock()
    ev_svc = ResearchEvidenceService(mock_repo)

    source = ResearchSource(
        id="src-valid-1",
        location="doc.txt",
        source_type=SourceType.INTERNAL_DOCUMENT,
        reliability_score=0.95,
    )
    mock_repo.get_source_by_id.return_value = source

    snippet = "Memory context construction takes 120ms on average."
    existing_evidence = ResearchEvidence(
        id="ev-orig-100",
        source_id="src-valid-1",
        content_snippet=snippet,
        integrity_hash=ev_svc.compute_integrity_hash(snippet),
        is_independent=True,
        corroboration_count=1,
    )

    # Simulate existing evidence in repository for exact same snippet
    mock_repo.get_evidence_by_hash.return_value = existing_evidence
    mock_repo.save_evidence.side_effect = lambda ev: ev

    ev_derivative = await ev_svc.add_evidence(
        source_id=source.id,
        content_snippet=snippet,
    )

    # Derivative snippet must NOT be marked independent
    assert ev_derivative.is_independent is False
    assert ev_derivative.corroboration_count == 2


@pytest.mark.asyncio
async def test_missing_question_plan_creation_failure():
    mock_repo = AsyncMock()
    plan_svc = ResearchPlanningService(mock_repo)

    mock_repo.get_question_by_id.return_value = None

    with pytest.raises(ValueError, match="Research question 'q-nonexistent' not found"):
        await plan_svc.create_research_plan(
            question_id="q-nonexistent",
            title="Orphan Plan",
            objective="Test missing parent question",
        )


@pytest.mark.asyncio
async def test_evaluate_nonexistent_hypothesis_failure():
    mock_repo = AsyncMock()
    hyp_svc = ResearchHypothesisService(mock_repo)

    mock_repo.get_hypothesis_by_id.return_value = None

    with pytest.raises(ValueError, match="Hypothesis 'hyp-ghost' not found"):
        await hyp_svc.evaluate_hypothesis_result(
            hypothesis_id="hyp-ghost",
            result_description="No hypothesis exists",
            conclusion="Should fail",
            is_supported=True,
        )
