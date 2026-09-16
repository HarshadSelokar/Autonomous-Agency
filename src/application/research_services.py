"""Application Services and Autonomous Discovery Engine for Phase 19 Research & Innovation."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any
import uuid

from src.domain.experiment import OrganizationalExperiment
from src.domain.knowledge import KnowledgeAuthority, KnowledgeItem, KnowledgeScope, KnowledgeStatus, KnowledgeType
from src.domain.research import (
    BenchmarkType,
    HypothesisStatus,
    InnovationProposal,
    InnovationType,
    OpportunityStatus,
    ResearchBenchmark,
    ResearchDiscovery,
    ResearchEvidence,
    ResearchFinding,
    ResearchHypothesis,
    ResearchOpportunity,
    ResearchPlan,
    ResearchProgram,
    ResearchQuestion,
    ResearchRequest,
    ResearchScope,
    ResearchSource,
    ResearchStatus,
    SourceType,
    TechnologyEvaluation,
)
from src.infrastructure.repositories.research_repository import SQLAlchemyResearchRepository

logger = logging.getLogger(__name__)


class ResearchPlanningService:
    """Decomposes research requests into questions, subquestions, plans, and capability demands."""

    def __init__(self, repository: SQLAlchemyResearchRepository) -> None:
        self.repo = repository

    async def create_request(
        self,
        question: str,
        purpose: str,
        scope: ResearchScope = ResearchScope.COMPANY,
        urgency: str = "MEDIUM",
        requester_id: str = "system",
        source_origin: str = "STRATEGY",
        governance_required: bool = False,
    ) -> ResearchRequest:
        req = ResearchRequest(
            question=question,
            purpose=purpose,
            scope=scope,
            urgency=urgency,
            requester_id=requester_id,
            source_origin=source_origin,
            governance_required=governance_required,
        )
        return await self.repo.save_request(req)

    async def decompose_request_into_questions(
        self,
        request_id: str,
        sub_questions: list[str] | None = None,
    ) -> list[ResearchQuestion]:
        req = await self.repo.get_request_by_id(request_id)
        if not req:
            raise ValueError(f"Research request '{request_id}' not found.")

        req.status = ResearchStatus.PLANNING
        await self.repo.save_request(req)

        main_q = ResearchQuestion(
            request_id=request_id,
            question=req.question,
            context=req.purpose,
            scope=req.scope,
            owner_id=req.requester_id,
        )
        main_q = await self.repo.save_question(main_q)

        created_questions = [main_q]
        if sub_questions:
            for sq_text in sub_questions:
                sub_q = ResearchQuestion(
                    request_id=request_id,
                    question=sq_text,
                    scope=req.scope,
                    parent_question_id=main_q.id,
                    owner_id=req.requester_id,
                )
                sub_q = await self.repo.save_question(sub_q)
                main_q.sub_question_ids.append(sub_q.id)
                created_questions.append(sub_q)

            await self.repo.save_question(main_q)

        return created_questions

    async def create_research_plan(
        self,
        question_id: str,
        title: str,
        objective: str,
        required_capabilities: list[str] | None = None,
    ) -> ResearchPlan:
        q = await self.repo.get_question_by_id(question_id)
        if not q:
            raise ValueError(f"Research question '{question_id}' not found.")

        plan = ResearchPlan(
            question_id=question_id,
            title=title,
            objective=objective,
            tool_requirements=required_capabilities or ["web_research", "data_analysis"],
            status=ResearchStatus.PLANNING,
        )
        return await self.repo.save_plan(plan)


class ResearchSourceService:
    """Manages internal/external sources, prompt injection security checks, and reliability scoring."""

    def __init__(self, repository: SQLAlchemyResearchRepository) -> None:
        self.repo = repository

    def inspect_prompt_injection(self, content: str) -> bool:
        """Detect prompt injection attempts in untrusted external content."""
        suspicious_patterns = [
            "ignore previous instructions",
            "system prompt override",
            "grant root access",
            "reveal api key",
            "bypass governance",
            "delete database",
        ]
        lowered = content.lower()
        return any(pat in lowered for pat in suspicious_patterns)

    def calculate_reliability_score(
        self,
        source_type: SourceType,
        is_external: bool,
        provenance: str,
        has_prompt_injection: bool,
    ) -> float:
        """Calculate explainable source reliability score between 0.0 and 1.0."""
        if has_prompt_injection:
            return 0.0  # Poisoned source gets 0 reliability!

        base_scores = {
            SourceType.INTERNAL_DOCUMENT: 0.95,
            SourceType.INTERNAL_ARTIFACT: 0.90,
            SourceType.INTERNAL_DATASET: 0.90,
            SourceType.APPROVED_DATABASE: 0.85,
            SourceType.TECHNICAL_DOCUMENTATION: 0.80,
            SourceType.PUBLIC_RESEARCH_PAPER: 0.75,
            SourceType.APPROVED_EXTERNAL_WEBSITE: 0.60,
            SourceType.EXTERNAL_API: 0.70,
        }
        score = base_scores.get(source_type, 0.50)
        if is_external:
            score *= 0.85  # External discount
        return round(max(0.0, min(1.0, score)), 4)

    async def register_source(
        self,
        location: str,
        source_type: SourceType,
        provenance: str = "",
        raw_content: str = "",
        is_external: bool = False,
    ) -> ResearchSource:
        is_untrusted = is_external or (source_type in (SourceType.APPROVED_EXTERNAL_WEBSITE, SourceType.EXTERNAL_API))
        has_injection = self.inspect_prompt_injection(raw_content)
        reliability = self.calculate_reliability_score(
            source_type=source_type,
            is_external=is_external,
            provenance=provenance,
            has_prompt_injection=has_injection,
        )

        src = ResearchSource(
            location=location,
            source_type=source_type,
            provenance=provenance,
            is_external=is_external,
            is_untrusted=is_untrusted,
            prompt_injection_checked=True,
            reliability_score=reliability,
        )
        return await self.repo.save_source(src)


class ResearchEvidenceService:
    """Extracts evidence, enforces source independence (deduplicates derivative sources), and creates findings."""

    def __init__(self, repository: SQLAlchemyResearchRepository) -> None:
        self.repo = repository

    def compute_integrity_hash(self, content_snippet: str) -> str:
        return hashlib.sha256(content_snippet.strip().encode("utf-8")).hexdigest()

    async def add_evidence(
        self,
        source_id: str,
        content_snippet: str,
        data_points: dict[str, Any] | None = None,
    ) -> ResearchEvidence:
        src = await self.repo.get_source_by_id(source_id)
        if not src:
            raise ValueError(f"Source '{source_id}' not found.")

        # Rejection of poisoned content
        if src.reliability_score <= 0.0:
            raise ValueError(f"Cannot extract evidence from poisoned source '{source_id}'!")

        hash_val = self.compute_integrity_hash(content_snippet)

        # Independence Check: If snippet hash already exists, mark as derivative (is_independent = False)
        existing_ev = await self.repo.get_evidence_by_hash(hash_val)
        is_independent = True if not existing_ev else False

        ev = ResearchEvidence(
            source_id=source_id,
            content_snippet=content_snippet,
            data_points=data_points or {},
            integrity_hash=hash_val,
            is_independent=is_independent,
            corroboration_count=1 if is_independent else (existing_ev.corroboration_count + 1 if existing_ev else 1),
        )
        return await self.repo.save_evidence(ev)

    async def synthesize_finding(
        self,
        question_id: str,
        finding_statement: str,
        evidence_ids: list[str],
        confidence: float = 0.80,
        researcher_id: str = "system",
    ) -> ResearchFinding:
        # Every finding MUST reference at least 1 evidence item
        if not evidence_ids:
            raise ValueError("Every research finding MUST reference at least 1 valid evidence item!")

        finding = ResearchFinding(
            question_id=question_id,
            finding_statement=finding_statement,
            evidence_ids=evidence_ids,
            confidence=confidence,
            researcher_id=researcher_id,
        )
        return await self.repo.save_finding(finding)


class ResearchHypothesisService:
    """Manages hypothesis lifecycle, benchmarks, technology evaluations, and Phase 18 Knowledge candidate promotion."""

    def __init__(
        self,
        repository: SQLAlchemyResearchRepository,
        knowledge_repository: Any | None = None,
        validation_service: Any | None = None,
    ) -> None:
        self.repo = repository
        self.knowledge_repo = knowledge_repository
        self.validation_svc = validation_service

    async def formulate_hypothesis(
        self,
        question_id: str,
        observation: str,
        statement: str,
        prediction: str,
    ) -> ResearchHypothesis:
        hyp = ResearchHypothesis(
            question_id=question_id,
            observation=observation,
            statement=statement,
            prediction=prediction,
            status=HypothesisStatus.PROPOSED,
        )
        return await self.repo.save_hypothesis(hyp)

    async def evaluate_hypothesis_result(
        self,
        hypothesis_id: str,
        result_description: str,
        conclusion: str,
        is_supported: bool,
    ) -> ResearchHypothesis:
        hyp = await self.repo.get_hypothesis_by_id(hypothesis_id)
        if not hyp:
            raise ValueError(f"Hypothesis '{hypothesis_id}' not found.")

        hyp.result = result_description
        hyp.conclusion = conclusion
        hyp.status = HypothesisStatus.SUPPORTED if is_supported else HypothesisStatus.REFUTED
        saved_hyp = await self.repo.save_hypothesis(hyp)

        # If supported, promote conclusion to Phase 18 Knowledge Candidate
        if is_supported and self.knowledge_repo:
            item = KnowledgeItem(
                statement=f"Research confirmed hypothesis '{hyp.statement}': {conclusion}",
                knowledge_type=KnowledgeType.FACT,
                scope=KnowledgeScope.COMPANY,
                confidence=0.85,
                status=KnowledgeStatus.CANDIDATE,
                authority=KnowledgeAuthority.UNVERIFIED,
            )
            await self.knowledge_repo.save_knowledge_item(item)

        return saved_hyp


class AutonomousDiscoveryEngine:
    """Listens to system events and automatically creates Research Discovery records & Research Requests."""

    def __init__(self, research_service: ResearchPlanningService) -> None:
        self.research_svc = research_service

    async def on_kpi_deviation(self, kpi_name: str, deviation_pct: float, entity_id: str) -> ResearchDiscovery:
        desc = f"KPI '{kpi_name}' deviated by {deviation_pct:.1f}% on entity {entity_id}"
        req = await self.research_svc.create_request(
            question=f"Why did KPI '{kpi_name}' deviate by {deviation_pct:.1f}%?",
            purpose=desc,
            urgency="HIGH" if abs(deviation_pct) > 20 else "MEDIUM",
            source_origin="KPI_DEVIATION",
        )
        disc = ResearchDiscovery(
            trigger_event="KPI_DEVIATION",
            trigger_entity_id=entity_id,
            description=desc,
            created_request_id=req.id,
        )
        return await self.research_svc.repo.save_discovery(disc)

    async def on_knowledge_gap_detected(self, topic: str, requester_id: str) -> ResearchDiscovery:
        desc = f"Knowledge gap detected regarding topic: '{topic}'"
        req = await self.research_svc.create_request(
            question=f"What are the authoritative facts and procedures for '{topic}'?",
            purpose=desc,
            requester_id=requester_id,
            source_origin="KNOWLEDGE_GAP",
        )
        disc = ResearchDiscovery(
            trigger_event="KNOWLEDGE_GAP",
            trigger_entity_id=topic,
            description=desc,
            created_request_id=req.id,
        )
        return await self.research_svc.repo.save_discovery(disc)


class InnovationEngineService:
    """Synthesizes research findings into opportunities, creates innovation proposals, and submits for Phase 11 Governance."""

    def __init__(
        self,
        repository: SQLAlchemyResearchRepository,
        governance_service: Any | None = None,
        company_repository: Any | None = None,
    ) -> None:
        self.repo = repository
        self.governance_svc = governance_service
        self.company_repo = company_repository

    async def identify_opportunity(
        self,
        finding_id: str,
        title: str,
        description: str,
        estimated_value_score: float = 0.80,
    ) -> ResearchOpportunity:
        opp = ResearchOpportunity(
            finding_id=finding_id,
            title=title,
            description=description,
            estimated_value_score=estimated_value_score,
            status=OpportunityStatus.IDENTIFIED,
        )
        return await self.repo.save_opportunity(opp)

    async def create_innovation_proposal(
        self,
        opportunity_id: str,
        title: str,
        innovation_type: InnovationType,
        problem_statement: str,
        proposed_solution: str,
        expected_value: str,
        evidence_ids: list[str],
        reversibility: str = "HIGH",
    ) -> InnovationProposal:
        opp = await self.repo.get_opportunity_by_id(opportunity_id)
        if not opp:
            raise ValueError(f"Opportunity '{opportunity_id}' not found.")

        opp.status = OpportunityStatus.PROPOSED
        await self.repo.save_opportunity(opp)

        prop = InnovationProposal(
            opportunity_id=opportunity_id,
            title=title,
            innovation_type=innovation_type,
            problem_statement=problem_statement,
            evidence_ids=evidence_ids,
            proposed_solution=proposed_solution,
            expected_value=expected_value,
            reversibility=reversibility,
            is_approved=False,
        )
        return await self.repo.save_proposal(prop)

    async def approve_proposal_by_governance(
        self,
        proposal_id: str,
        governance_request_id: str,
    ) -> InnovationProposal:
        prop = await self.repo.get_proposal_by_id(proposal_id)
        if not prop:
            raise ValueError(f"Innovation proposal '{proposal_id}' not found.")

        prop.is_approved = True
        prop.governance_request_id = governance_request_id
        prop.strategic_initiative_id = f"init-inno-{uuid.uuid4().hex[:8]}"
        saved_prop = await self.repo.save_proposal(prop)

        # Update underlying opportunity status
        opp = await self.repo.get_opportunity_by_id(prop.opportunity_id)
        if opp:
            opp.status = OpportunityStatus.APPROVED
            await self.repo.save_opportunity(opp)

        return saved_prop
