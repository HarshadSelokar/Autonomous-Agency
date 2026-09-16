"""SQLAlchemy Repository Implementation for Phase 19 Research & Innovation."""

from collections.abc import Sequence
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.infrastructure.models.research_model import (
    InnovationProposalModel,
    ResearchBenchmarkModel,
    ResearchDiscoveryModel,
    ResearchEvidenceModel,
    ResearchFindingModel,
    ResearchHypothesisModel,
    ResearchOpportunityModel,
    ResearchPlanModel,
    ResearchProgramModel,
    ResearchQuestionModel,
    ResearchRequestModel,
    ResearchSourceModel,
    TechnologyEvaluationModel,
)


class SQLAlchemyResearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Programs ---
    async def save_program(self, program: ResearchProgram) -> ResearchProgram:
        model = ResearchProgramModel(
            id=program.id,
            title=program.title,
            purpose=program.purpose,
            scope=program.scope.value if hasattr(program.scope, "value") else str(program.scope),
            owner_id=program.owner_id,
            status=program.status.value if hasattr(program.status, "value") else str(program.status),
            research_question_ids={"items": program.research_question_ids},
            findings_ids={"items": program.findings_ids},
            knowledge_item_ids={"items": program.knowledge_item_ids},
            created_at=program.created_at,
            updated_at=program.updated_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return program

    async def get_program_by_id(self, program_id: str) -> ResearchProgram | None:
        stmt = select(ResearchProgramModel).where(ResearchProgramModel.id == program_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return ResearchProgram(
            id=model.id,
            title=model.title,
            purpose=model.purpose,
            scope=ResearchScope(model.scope),
            owner_id=model.owner_id,
            status=ResearchStatus(model.status),
            research_question_ids=model.research_question_ids.get("items", []) if model.research_question_ids else [],
            findings_ids=model.findings_ids.get("items", []) if model.findings_ids else [],
            knowledge_item_ids=model.knowledge_item_ids.get("items", []) if model.knowledge_item_ids else [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_programs(self) -> list[ResearchProgram]:
        stmt = select(ResearchProgramModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ResearchProgram(
                id=m.id,
                title=m.title,
                purpose=m.purpose,
                scope=ResearchScope(m.scope),
                owner_id=m.owner_id,
                status=ResearchStatus(m.status),
                research_question_ids=m.research_question_ids.get("items", []) if m.research_question_ids else [],
                findings_ids=m.findings_ids.get("items", []) if m.findings_ids else [],
                knowledge_item_ids=m.knowledge_item_ids.get("items", []) if m.knowledge_item_ids else [],
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    # --- Requests ---
    async def save_request(self, req: ResearchRequest) -> ResearchRequest:
        model = ResearchRequestModel(
            id=req.id,
            question=req.question,
            purpose=req.purpose,
            scope=req.scope.value if hasattr(req.scope, "value") else str(req.scope),
            urgency=req.urgency.value if hasattr(req.urgency, "value") else str(req.urgency),
            requester_id=req.requester_id,
            source_origin=req.source_origin,
            expected_output=req.expected_output,
            constraints=req.constraints,
            evidence_requirements={"items": req.evidence_requirements},
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
            governance_required=req.governance_required,
            created_at=req.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return req

    async def get_request_by_id(self, request_id: str) -> ResearchRequest | None:
        stmt = select(ResearchRequestModel).where(ResearchRequestModel.id == request_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchRequest(
            id=m.id,
            question=m.question,
            purpose=m.purpose,
            scope=ResearchScope(m.scope),
            urgency=m.urgency,
            requester_id=m.requester_id,
            source_origin=m.source_origin,
            expected_output=m.expected_output,
            constraints=m.constraints or {},
            evidence_requirements=m.evidence_requirements.get("items", []) if m.evidence_requirements else [],
            status=ResearchStatus(m.status),
            governance_required=m.governance_required,
            created_at=m.created_at,
        )

    async def list_requests() -> list[ResearchRequest]:
        stmt = select(ResearchRequestModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ResearchRequest(
                id=m.id,
                question=m.question,
                purpose=m.purpose,
                scope=ResearchScope(m.scope),
                urgency=m.urgency,
                requester_id=m.requester_id,
                source_origin=m.source_origin,
                expected_output=m.expected_output,
                constraints=m.constraints or {},
                evidence_requirements=m.evidence_requirements.get("items", []) if m.evidence_requirements else [],
                status=ResearchStatus(m.status),
                governance_required=m.governance_required,
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Questions ---
    async def save_question(self, q: ResearchQuestion) -> ResearchQuestion:
        model = ResearchQuestionModel(
            id=q.id,
            request_id=q.request_id,
            question=q.question,
            context=q.context,
            assumptions={"items": q.assumptions},
            scope=q.scope.value if hasattr(q.scope, "value") else str(q.scope),
            evidence_requirements={"items": q.evidence_requirements},
            success_criteria=q.success_criteria,
            parent_question_id=q.parent_question_id,
            sub_question_ids={"items": q.sub_question_ids},
            owner_id=q.owner_id,
            status=q.status.value if hasattr(q.status, "value") else str(q.status),
            created_at=q.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return q

    async def get_question_by_id(self, question_id: str) -> ResearchQuestion | None:
        stmt = select(ResearchQuestionModel).where(ResearchQuestionModel.id == question_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchQuestion(
            id=m.id,
            request_id=m.request_id,
            question=m.question,
            context=m.context,
            assumptions=m.assumptions.get("items", []) if m.assumptions else [],
            scope=ResearchScope(m.scope),
            evidence_requirements=m.evidence_requirements.get("items", []) if m.evidence_requirements else [],
            success_criteria=m.success_criteria or {},
            parent_question_id=m.parent_question_id,
            sub_question_ids=m.sub_question_ids.get("items", []) if m.sub_question_ids else [],
            owner_id=m.owner_id,
            status=ResearchStatus(m.status),
            created_at=m.created_at,
        )

    # --- Plans ---
    async def save_plan(self, plan: ResearchPlan) -> ResearchPlan:
        model = ResearchPlanModel(
            id=plan.id,
            question_id=plan.question_id,
            title=plan.title,
            objective=plan.objective,
            task_ids={"items": plan.task_ids},
            assigned_employee_ids={"items": plan.assigned_employee_ids},
            assigned_team_id=plan.assigned_team_id,
            tool_requirements={"items": plan.tool_requirements},
            status=plan.status.value if hasattr(plan.status, "value") else str(plan.status),
            created_at=plan.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return plan

    async def get_plan_by_id(self, plan_id: str) -> ResearchPlan | None:
        stmt = select(ResearchPlanModel).where(ResearchPlanModel.id == plan_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchPlan(
            id=m.id,
            question_id=m.question_id,
            title=m.title,
            objective=m.objective,
            task_ids=m.task_ids.get("items", []) if m.task_ids else [],
            assigned_employee_ids=m.assigned_employee_ids.get("items", []) if m.assigned_employee_ids else [],
            assigned_team_id=m.assigned_team_id,
            tool_requirements=m.tool_requirements.get("items", []) if m.tool_requirements else [],
            status=ResearchStatus(m.status),
            created_at=m.created_at,
        )

    # --- Sources & Evidence ---
    async def save_source(self, src: ResearchSource) -> ResearchSource:
        model = ResearchSourceModel(
            id=src.id,
            location=src.location,
            source_type=src.source_type.value if hasattr(src.source_type, "value") else str(src.source_type),
            access_method=src.access_method,
            provenance=src.provenance,
            is_external=src.is_external,
            is_untrusted=src.is_untrusted,
            prompt_injection_checked=src.prompt_injection_checked,
            reliability_score=src.reliability_score,
            retrieved_at=src.retrieved_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return src

    async def get_source_by_id(self, source_id: str) -> ResearchSource | None:
        stmt = select(ResearchSourceModel).where(ResearchSourceModel.id == source_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchSource(
            id=m.id,
            location=m.location,
            source_type=SourceType(m.source_type),
            access_method=m.access_method,
            provenance=m.provenance,
            is_external=m.is_external,
            is_untrusted=m.is_untrusted,
            prompt_injection_checked=m.prompt_injection_checked,
            reliability_score=m.reliability_score,
            retrieved_at=m.retrieved_at,
        )

    async def save_evidence(self, ev: ResearchEvidence) -> ResearchEvidence:
        model = ResearchEvidenceModel(
            id=ev.id,
            source_id=ev.source_id,
            content_snippet=ev.content_snippet,
            data_points=ev.data_points,
            integrity_hash=ev.integrity_hash,
            is_independent=ev.is_independent,
            corroboration_count=ev.corroboration_count,
            created_at=ev.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return ev

    async def get_evidence_by_id(self, evidence_id: str) -> ResearchEvidence | None:
        stmt = select(ResearchEvidenceModel).where(ResearchEvidenceModel.id == evidence_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchEvidence(
            id=m.id,
            source_id=m.source_id,
            content_snippet=m.content_snippet,
            data_points=m.data_points or {},
            integrity_hash=m.integrity_hash,
            is_independent=m.is_independent,
            corroboration_count=m.corroboration_count,
            created_at=m.created_at,
        )

    async def get_evidence_by_hash(self, integrity_hash: str) -> ResearchEvidence | None:
        stmt = select(ResearchEvidenceModel).where(ResearchEvidenceModel.integrity_hash == integrity_hash)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchEvidence(
            id=m.id,
            source_id=m.source_id,
            content_snippet=m.content_snippet,
            data_points=m.data_points or {},
            integrity_hash=m.integrity_hash,
            is_independent=m.is_independent,
            corroboration_count=m.corroboration_count,
            created_at=m.created_at,
        )

    # --- Findings & Hypotheses ---
    async def save_finding(self, finding: ResearchFinding) -> ResearchFinding:
        model = ResearchFindingModel(
            id=finding.id,
            question_id=finding.question_id,
            finding_statement=finding.finding_statement,
            evidence_ids={"items": finding.evidence_ids},
            scope=finding.scope.value if hasattr(finding.scope, "value") else str(finding.scope),
            confidence=finding.confidence,
            assumptions={"items": finding.assumptions},
            limitations={"items": finding.limitations},
            researcher_id=finding.researcher_id,
            created_at=finding.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return finding

    async def get_finding_by_id(self, finding_id: str) -> ResearchFinding | None:
        stmt = select(ResearchFindingModel).where(ResearchFindingModel.id == finding_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchFinding(
            id=m.id,
            question_id=m.question_id,
            finding_statement=m.finding_statement,
            evidence_ids=m.evidence_ids.get("items", []) if m.evidence_ids else [],
            scope=ResearchScope(m.scope),
            confidence=m.confidence,
            assumptions=m.assumptions.get("items", []) if m.assumptions else [],
            limitations=m.limitations.get("items", []) if m.limitations else [],
            researcher_id=m.researcher_id,
            created_at=m.created_at,
        )

    async def save_hypothesis(self, hyp: ResearchHypothesis) -> ResearchHypothesis:
        model = ResearchHypothesisModel(
            id=hyp.id,
            question_id=hyp.question_id,
            observation=hyp.observation,
            statement=hyp.statement,
            prediction=hyp.prediction,
            status=hyp.status.value if hasattr(hyp.status, "value") else str(hyp.status),
            experiment_id=hyp.experiment_id,
            result=hyp.result,
            conclusion=hyp.conclusion,
            created_at=hyp.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return hyp

    async def get_hypothesis_by_id(self, hypothesis_id: str) -> ResearchHypothesis | None:
        stmt = select(ResearchHypothesisModel).where(ResearchHypothesisModel.id == hypothesis_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchHypothesis(
            id=m.id,
            question_id=m.question_id,
            observation=m.observation,
            statement=m.statement,
            prediction=m.prediction,
            status=HypothesisStatus(m.status),
            experiment_id=m.experiment_id,
            result=m.result,
            conclusion=m.conclusion,
            created_at=m.created_at,
        )

    # --- Opportunities & Proposals ---
    async def save_opportunity(self, opp: ResearchOpportunity) -> ResearchOpportunity:
        model = ResearchOpportunityModel(
            id=opp.id,
            finding_id=opp.finding_id,
            title=opp.title,
            description=opp.description,
            status=opp.status.value if hasattr(opp.status, "value") else str(opp.status),
            estimated_value_score=opp.estimated_value_score,
            created_at=opp.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return opp

    async def get_opportunity_by_id(self, opp_id: str) -> ResearchOpportunity | None:
        stmt = select(ResearchOpportunityModel).where(ResearchOpportunityModel.id == opp_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ResearchOpportunity(
            id=m.id,
            finding_id=m.finding_id,
            title=m.title,
            description=m.description,
            status=OpportunityStatus(m.status),
            estimated_value_score=m.estimated_value_score,
            created_at=m.created_at,
        )

    async def save_proposal(self, prop: InnovationProposal) -> InnovationProposal:
        model = InnovationProposalModel(
            id=prop.id,
            opportunity_id=prop.opportunity_id,
            title=prop.title,
            innovation_type=prop.innovation_type.value if hasattr(prop.innovation_type, "value") else str(prop.innovation_type),
            problem_statement=prop.problem_statement,
            evidence_ids={"items": prop.evidence_ids},
            proposed_solution=prop.proposed_solution,
            expected_value=prop.expected_value,
            required_capabilities={"items": prop.required_capabilities},
            required_resources=prop.required_resources,
            risks={"items": prop.risks},
            reversibility=prop.reversibility,
            governance_request_id=prop.governance_request_id,
            is_approved=prop.is_approved,
            strategic_initiative_id=prop.strategic_initiative_id,
            created_at=prop.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return prop

    async def get_proposal_by_id(self, proposal_id: str) -> InnovationProposal | None:
        stmt = select(InnovationProposalModel).where(InnovationProposalModel.id == proposal_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return InnovationProposal(
            id=m.id,
            opportunity_id=m.opportunity_id,
            title=m.title,
            innovation_type=InnovationType(m.innovation_type),
            problem_statement=m.problem_statement,
            evidence_ids=m.evidence_ids.get("items", []) if m.evidence_ids else [],
            proposed_solution=m.proposed_solution,
            expected_value=m.expected_value,
            required_capabilities=m.required_capabilities.get("items", []) if m.required_capabilities else [],
            required_resources=m.required_resources or {},
            risks=m.risks.get("items", []) if m.risks else [],
            reversibility=m.reversibility,
            governance_request_id=m.governance_request_id,
            is_approved=m.is_approved,
            strategic_initiative_id=m.strategic_initiative_id,
            created_at=m.created_at,
        )

    async def list_proposals() -> list[InnovationProposal]:
        stmt = select(InnovationProposalModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            InnovationProposal(
                id=m.id,
                opportunity_id=m.opportunity_id,
                title=m.title,
                innovation_type=InnovationType(m.innovation_type),
                problem_statement=m.problem_statement,
                evidence_ids=m.evidence_ids.get("items", []) if m.evidence_ids else [],
                proposed_solution=m.proposed_solution,
                expected_value=m.expected_value,
                required_capabilities=m.required_capabilities.get("items", []) if m.required_capabilities else [],
                required_resources=m.required_resources or {},
                risks=m.risks.get("items", []) if m.risks else [],
                reversibility=m.reversibility,
                governance_request_id=m.governance_request_id,
                is_approved=m.is_approved,
                strategic_initiative_id=m.strategic_initiative_id,
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Discoveries, Benchmarks & Technology Evaluations ---
    async def save_discovery(self, disc: ResearchDiscovery) -> ResearchDiscovery:
        model = ResearchDiscoveryModel(
            id=disc.id,
            trigger_event=disc.trigger_event,
            trigger_entity_id=disc.trigger_entity_id,
            description=disc.description,
            created_request_id=disc.created_request_id,
            created_at=disc.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return disc

    async def save_benchmark(self, bench: ResearchBenchmark) -> ResearchBenchmark:
        model = ResearchBenchmarkModel(
            id=bench.id,
            benchmark_type=bench.benchmark_type.value if hasattr(bench.benchmark_type, "value") else str(bench.benchmark_type),
            target_name=bench.target_name,
            workload_description=bench.workload_description,
            metrics=bench.metrics,
            environment=bench.environment,
            limitations={"items": bench.limitations},
            evaluated_at=bench.evaluated_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return bench

    async def save_technology_evaluation(self, eval_item: TechnologyEvaluation) -> TechnologyEvaluation:
        model = TechnologyEvaluationModel(
            id=eval_item.id,
            candidate_technology=eval_item.candidate_technology,
            category=eval_item.category,
            benchmark_ids={"items": eval_item.benchmark_ids},
            security_review_summary=eval_item.security_review_summary,
            cost_analysis=eval_item.cost_analysis,
            operational_feasibility=eval_item.operational_feasibility,
            recommendation=eval_item.recommendation,
            governance_approval_id=eval_item.governance_approval_id,
            created_at=eval_item.created_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return eval_item
